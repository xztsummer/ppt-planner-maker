用户不手动指定skill时，项目默认执行 'skills\ppt-planner-maker' 这个skill。
- Windows 中文路径下，临时 PowerShell 脚本必须保存为 UTF-8 with BOM，或改用 Python / `-EncodedCommand`；无 BOM 的 UTF-8 会被 PowerShell 5.1 按 GBK 读取，可能吞掉路径分隔符并生成乱码目录。