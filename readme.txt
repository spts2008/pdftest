命令行执行：
pdftest.exe  5.pdf 0.8 release
参数说明：
 5.pdf---pdf路径
0.8-- 阈值 
release--模式


待比对的图片放在baseimgs目录下

打包：
pyinstaller -F pypdftest.py	