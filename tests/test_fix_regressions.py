"""Offline regressions for the end-to-end findings."""
import io
import json
import os
import sys
import tempfile
import unittest
import zipfile
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import clean_deck as cd
import setup as st
import verify_deck as vd
import doctor
from test_setup import fake_deps, MISSING
from resolve_skills import build_roots, load_deps


class Regressions(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)

    def plan(self, explicit, state, target_exists=False):
        deps = load_deps(fake_deps(self.base, [MISSING], "a" * 40))
        target = self.base / "private" / "skills"
        old = self.base / "ws" / ".agents" / "skills" / "fake-skill"
        for path in [old] + ([target / "fake-skill"] if target_exists else []):
            path.mkdir(parents=True)
            (path / "SKILL.md").write_text("---\nname: fake-skill\n---\n")
            (path / "requirements.txt").write_text("old-dependency")
        roots = build_roots(self.base / "ws", [target] if explicit else [], self.base / "h1", self.base / "h2", self.base / "h3")
        with mock.patch('resolve_skills.version_drift', return_value={"state": state, "installed": "old", "tested": "a"*40}):
            return st.build_plan_for_run(deps, deps['skills'], roots, self.base / 'ws', ['A'], target, True, explicit_target=explicit)

    def test_old_copy_empty_explicit_target(self):
        plan = self.plan(True, 'drift')
        self.assertEqual(len(plan['clone']), 1)
        self.assertFalse(plan['ready'])
        self.assertIn(str(self.base / 'private'), plan['pip'][0]['cmd'][-1])
        self.assertTrue(any('其他位置' in w for w in plan['warnings']))

    def test_setup_environment_root_warns_without_changing_install_target(self):
        env_root = self.base / 'env-skills'
        old = env_root / 'fake-skill'
        old.mkdir(parents=True)
        (old / 'SKILL.md').write_text('---\nname: fake-skill\nversion: 6.7.3\n---\n', encoding='utf-8')
        (old / 'VERSION').write_text('6.7.3', encoding='utf-8')
        workspace = self.base / 'workspace'
        workspace.mkdir()
        deps = fake_deps(self.base, tested_version='a'*40)
        data = json.loads(deps.read_text(encoding='utf-8'))
        data['skills'][0]['testedRelease'] = '6.8.0'
        deps.write_text(json.dumps(data), encoding='utf-8')
        private = self.base / 'private'
        for explicit in [False, True]:
            with self.subTest(explicit=explicit):
                out = io.StringIO()
                flags = ['--skills-dir',str(self.base/'explicit-target')] if explicit else []
                env = {'PPT_PLANNER_SKILLS_DIR':str(env_root),'PPT_PLANNER_HOME':str(private)}
                with mock.patch.dict(os.environ, env), redirect_stdout(out):
                    code = st.main(['--workspace',str(workspace),'--deps-file',str(deps),'--json',*flags])
                self.assertEqual(code,0)
                plan = json.loads(out.getvalue())
                target = self.base/'explicit-target' if explicit else private/'skills'
                self.assertEqual(Path(plan['targetRoot']),target)
                self.assertEqual(Path(plan['clone'][0]['target']), target/'fake-skill')
                warnings = '\n'.join(plan['warnings'])
                self.assertIn(str(old),warnings)
                self.assertNotIn("'state':",warnings)
                if not explicit:
                    self.assertIn('仍会抢占',warnings)
                    self.assertIn('已装 6.7.3，已测 6.8.0',warnings)
                    self.assertIn(f'将安装到 {target}',warnings)
        self.assertFalse(private.exists())

    def test_setup_unknown_warning_and_conflict_use_plain_language(self):
        plan = self.plan(False,'unknown')
        warning = next(w for w in plan['warnings'] if '旧副本' in w)
        self.assertIn('版本未知',warning)
        self.assertNotIn("'state':",warning)
        self.assertIn('将安装到',warning)
        self.assertEqual(st._version_description({'testedRelease':'6.8.0'}, {'version':'6.7.3','drift':{'state':'drift'}}), '已装 6.7.3，已测 6.8.0')

    def test_default_drift_and_unknown_clone_and_warn_shadowing(self):
        for state in ['drift', 'unknown']:
            with self.subTest(state=state):
                # Separate fixtures for each state.
                if (self.base / 'ws').exists():
                    import shutil
                    shutil.rmtree(self.base / 'ws')
                plan = self.plan(False, state)
                self.assertEqual(len(plan['clone']), 1)
                self.assertTrue(any('抢占' in w for w in plan['warnings']))

    def test_matching_default_reuses_copy(self):
        plan = self.plan(False, 'match')
        self.assertFalse(plan['clone'])
        self.assertEqual(plan['ready'], ['fake-skill'])

    def test_conflicting_target_is_manual_without_mutations(self):
        plan = self.plan(True, 'drift', True)
        self.assertTrue(plan['manual'])
        for key in ['clone', 'pin', 'pip']:
            self.assertFalse(plan[key])

    def test_run_order_requirements_after_pin_and_pip_environment(self):
        root = self.base / 'skill'
        root.mkdir()
        plan = {'clone': [{'id':'s','cmd':['clone']}], 'pin':[{'id':'s','cmd':['pin']}], 'pip':[{'id':'s','cmd':['pip'], 'runtimeRoot':str(root), 'packages':['yaml']}], 'manual':[]}
        calls = []
        def run(cmd, **kwargs):
            calls.append((cmd, kwargs))
            if cmd == ['pin']:
                (root / 'requirements.txt').write_text('PyYAML')
            if len(calls) == 3:
                self.assertEqual(kwargs['env']['PYYAML_FORCE_LIBYAML'], '0')
            return mock.Mock(returncode=0)
        with mock.patch.object(st.subprocess, 'run', side_effect=run), redirect_stdout(io.StringIO()):
            self.assertTrue(st._run_actions(plan))
        self.assertEqual([c[0] for c in calls[:2]], [['clone'], ['pin']])
        self.assertIn('PyYAML', st._pip_failure_hint(['pip','-r','requirements.txt']))

    def test_failed_clone_skips_pin_and_pip(self):
        plan = {k:[{'id':'s','cmd':[k]}] for k in ['clone','pin','pip']}
        with mock.patch.object(st.subprocess, 'run', return_value=mock.Mock(returncode=1)) as run, redirect_stdout(io.StringIO()):
            self.assertFalse(st._run_actions(plan))
        self.assertEqual(run.call_count, 1)

    def test_doctor_drift_unknown_prints_usable_setup_command(self):
        for state in ['drift', 'unknown']:
            result = {'workspace':str(self.base), 'branches':['B'], 'skills':{'s':{'id':'s','root':str(self.base),'status':'ok','drift':{'state':state}}}, 'runtime':{'checks':{'s':{'status':'ok'}}}, 'warnings':[]}
            out = io.StringIO()
            with redirect_stdout(out): doctor._print_human(result)
            self.assertIn('setup.py" --workspace', out.getvalue())
            self.assertIn('--branches B --skills-dir', out.getvalue())

    def test_doctor_old_copy_has_only_setup_next_step_and_match_keeps_pip(self):
        for state,status in [('drift','ok'),('unknown','ok'),('drift','incomplete'),('unknown','incomplete'),('match','ok')]:
            with self.subTest(state=state,status=status):
                item = {'id':'s','root':str(self.base/'old-copy'),'status':status,'drift':{'state':state},'install':'old path install hint'}
                runtime = {'status':'incomplete','missingRequired':['yaml'],'install':'python -m pip install -r <s>/requirements.txt'}
                result = {'workspace':str(self.base),'branches':['B'],'skills':{'s':item},'runtime':{'checks':{'s':runtime}},'warnings':[]}
                out = io.StringIO()
                with redirect_stdout(out): doctor._print_human(result)
                output = out.getvalue()
                self.assertEqual(output.count('下一步:'),1)
                self.assertIn('missing packages: yaml',output)
                if state == 'match':
                    self.assertIn(f'pip install -r {self.base / "old-copy/requirements.txt"}',output)
                    self.assertNotIn('setup.py',output)
                else:
                    self.assertIn('setup.py',output)
                    self.assertNotIn('pip install -r',output)
                    self.assertNotIn('old path install hint',output)

    def test_clean_brief_is_one_line_default_lists_removed_parts(self):
        source = self.base/'in.pptx'
        with zipfile.ZipFile(source,'w') as z:
            z.writestr('_rels/.rels','<Relationships><Relationship Target="ppt/presentation.xml"/></Relationships>')
            z.writestr('ppt/presentation.xml','<p:presentation xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"/>')
            z.writestr('[Content_Types].xml','<Types/>')
            z.writestr('unused.bin',b'orphan')
        for brief in [True,False]:
            out = io.StringIO()
            args = [str(source),'--out',str(self.base/f'out-{brief}.pptx')] + (['--brief'] if brief else [])
            with redirect_stdout(out):
                code = cd.main(args)
            self.assertEqual(code,0)
            lines = out.getvalue().splitlines()
            self.assertIn('removed=1',lines[0])
            self.assertIn('bytes',lines[0])
            if brief:
                self.assertEqual(len(lines),1)
                self.assertNotIn('unused.bin',out.getvalue())
            else:
                self.assertIn('unused.bin',lines[1:])

    def test_orphans_without_placeholders_warn(self):
        from test_verify_deck import build_pptx, text_slide
        path = self.base / 'deck.pptx'
        build_pptx(path, [text_slide('real')], orphans=(text_slide('unused'),))
        report = vd.verify(path,1,[],[])
        self.assertEqual(report.status, 'PASS')
        self.assertEqual(report.count('WARN'),1)

    def test_css_recursion_relative_paths_imports_urls_and_cycles(self):
        (self.base / 'css').mkdir()
        html = self.base / 'deck.html'
        html.write_text('<html><link rel="stylesheet" href="css/a.css"><style>@import "css/b.css";</style><section>Done</section></html>')
        (self.base / 'css/a.css').write_text('@import "b.css"; body{background:url(ok.png)}')
        (self.base / 'css/b.css').write_text('@import url(a.css); @import "https://fonts.example/a"; x{background:url(missing.png)}')
        (self.base / 'css/ok.png').write_bytes(b'ok')
        report = vd.verify(html, 1, [], [])
        self.assertEqual(report.count('FAIL'), 1)
        self.assertEqual(report.count('WARN'), 1)

    def test_extensionless_stylesheets_and_imports(self):
        html = self.base / 'deck.html'
        html.write_text('<html><link rel="stylesheet" href="style"><section>OK</section></html>')
        (self.base/'style').write_text('@import url(other);')
        (self.base/'other').write_text('x{background:url(missing.png)}')
        report = vd.verify(html,1,[],[])
        self.assertEqual(report.count('FAIL'),1)

    def test_clean_graph_preserves_bytes_shared_parts_and_metadata(self):
        source, out = self.base / 'in.pptx', self.base / 'out.pptx'
        rel = lambda targets: '<Relationships>' + ''.join(f'<Relationship Target="{t}"/>' for t in targets) + '</Relationships>'
        parts = {
            '_rels/.rels':rel(['ppt/presentation.xml','docProps/app.xml']),
            'ppt/presentation.xml':'<p:presentation xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"><p:sldIdLst><p:sldId id="1"/></p:sldIdLst><x:sectionLst xmlns:x="test"><x:sldId id="1"/><x:sldId id="2"/></x:sectionLst></p:presentation>',
            'ppt/_rels/presentation.xml.rels':rel(['slides/slide1.xml']),
            'ppt/slides/slide1.xml':'retained exactly',
            'ppt/slides/_rels/slide1.xml.rels':rel(['../media/shared.png']),
            'ppt/slides/slide2.xml':'orphan',
            'ppt/slides/_rels/slide2.xml.rels':rel(['../media/shared.png','../media/only.png','../notesSlides/notesSlide2.xml']),
            'ppt/media/shared.png':'shared', 'ppt/media/only.png':'orphan',
            'ppt/notesSlides/notesSlide2.xml':'orphan notes',
            'docProps/app.xml':'<Properties><Slides>2</Slides><HeadingPairs><old/></HeadingPairs><TitlesOfParts><old/></TitlesOfParts></Properties>',
        }
        parts['[Content_Types].xml'] = '<Types>' + ''.join(f'<Override PartName="/{k}" ContentType="test"/>' for k in parts if not k.endswith('.rels')) + '</Types>'
        with zipfile.ZipFile(source,'w') as z:
            for name, data in parts.items(): z.writestr(name,data)
        result = cd.clean(source,out)
        with zipfile.ZipFile(out) as z:
            for name in z.namelist():
                if name not in ['[Content_Types].xml','ppt/presentation.xml','docProps/app.xml']:
                    self.assertEqual(z.read(name), parts[name].encode())
            self.assertIn('ppt/media/shared.png', z.namelist())
            self.assertNotIn('ppt/media/only.png', z.namelist())
            self.assertNotIn(b'slide2.xml', z.read('[Content_Types].xml'))
            self.assertNotIn(b'id="2"',z.read('ppt/presentation.xml'))
            self.assertIn(b'<Slides>1</Slides>',z.read('docProps/app.xml'))
        self.assertEqual(len(result['removed']),4)
        with self.assertRaises(ValueError): cd.clean(source,source)

    def test_stale_slide_relationship_removed_before_graph_walk(self):
        source,out = self.base/'in.pptx',self.base/'out.pptx'
        with zipfile.ZipFile(source,'w') as z:
            z.writestr('_rels/.rels','<Relationships><Relationship Target="ppt/presentation.xml"/></Relationships>')
            z.writestr('ppt/presentation.xml','<p:presentation xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><p:sldIdLst><p:sldId id="1" r:id="live"/></p:sldIdLst></p:presentation>')
            z.writestr('ppt/_rels/presentation.xml.rels','<Relationships><Relationship Id="live" Type="x/slide" Target="slides/slide1.xml"/><Relationship Id="dead" Type="x/slide" Target="slides/slide2.xml"/></Relationships>')
            z.writestr('ppt/slides/slide1.xml','live')
            z.writestr('ppt/slides/slide2.xml','dead')
            z.writestr('[Content_Types].xml','<Types/>')
        cd.clean(source,out)
        with zipfile.ZipFile(out) as z:
            self.assertNotIn('ppt/slides/slide2.xml',z.namelist())
            self.assertNotIn(b'dead',z.read('ppt/_rels/presentation.xml.rels'))
