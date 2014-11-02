Installing MeCab and the Python Binding
=======================================

MeCab is a Japanese Morphological Analyser which will be used to break a Japanese sentence into its separate deinflected words. More information can be found here: http://mecab.googlecode.com/svn/trunk/mecab/doc/index.html

Mac OS X
--------

You can use
```sudo port install py27-mecab``` or adapt the installation guide for Linux for a Mac environment.

Linux (Ubuntu)
--------------

Make sure iconv is already installed.

Download and install [mecab-0.994](http://code.google.com/p/mecab/downloads/list):

```
wget https://mecab.googlecode.com/files/mecab-0.994.tar.gz
tar zxfv mecab-0.994.tar.gz
cd mecab-0.994
./configure --with-charset=utf8 --enable-utf8-only
```

If you get a g++ related error, try ```sudo apt-get install build-essential```.

```
make
sudo make install
```

Download and install [mecab-ipadic-2.7.0-20070801.tar.gz]( http://code.google.com/p/mecab/downloads/list):

```
wget https://mecab.googlecode.com/files/mecab-ipadic-2.7.0-20070801.tar.gz
tar zxfv mecab-ipadic-2.7.0-20070801.tar.gz
cd mecab-ipadic-2.7.0-20070801
./configure --with-charset=utf8
```

If you get a cannot open shared object file error, try ```sudo ldconfig```

```
make
sudo make install
```

Now test if the command line program works:
```
% mecab
今日もしないとね。
今日    名詞,副詞可能,*,*,*,*,今日,キョウ,キョー
も      助詞,係助詞,*,*,*,*,も,モ,モ
し      動詞,自立,*,*,サ変・スル,未然形,する,シ,シ
ない    助動詞,*,*,*,特殊・ナイ,基本形,ない,ナイ,ナイ
と      助詞,接続助詞,*,*,*,*,と,ト,ト
ね      助詞,終助詞,*,*,*,*,ね,ネ,ネ
。      
EOS
```

Download [mecab-python-0.994.tar.gz]( http://code.google.com/p/mecab/downloads/list):

```
wget https://mecab.googlecode.com/files/mecab-python-0.994.tar.gz
tar zxfv mecab-python-0.994.tar.gz
cd mecab-python-0.994
python setup.py build
```

If you get ```fatal error: Python.h: No such file or directory```, you need to ```sudo apt-get install python-dev```.

```
sudo python setup.py install
```

Now test if the binding installed correctly:
```
python test.py
```


Windows
-------

If you are running 64-bit Windows, make sure you are using 32-bit Python or it will not work.

It is advisable to [change the system locale to Japanese](http://windows.microsoft.com/en-au/windows/change-system-locale) to ensure the characters appear correctly. When you change the locale, you must reboot your system; otherwise, you may see unexpected locale-setting behaviors.

 - Download the MeCab Windows Binary [mecab-0.994.exe]( http://code.google.com/p/mecab/downloads/list).

 - Install MeCab and select UTF-8 encoding when prompted.

 - Append the MeCab directories to your [PATH](http://www.computerhope.com/issues/ch000549.htm):
```
C:\Program Files\MeCab\bin;C:\Program Files\MeCab\sdk;
```

 - If you are running 32-bit Windows, install Visual C++ 2008 Express (free download):

   http://www.microsoft.com/en-us/download/details.aspx?id=6506

   Later versions of Visual C++ will not work.

 - If you are running 64-bit Windows, install Visual C++ 2008 Professional

   http://www.microsoft.com/en-us/download/details.aspx?id=3713 (90 day trial)

 - Reboot your system.

 - You may need to install the Python setuptools if you haven't already installed it. We need this to install Python modules:

   http://pypi.python.org/pypi/setuptools

   http://stackoverflow.com/questions/309412/how-to-setup-setuptools-for-python-2-6-on-windows

 - Download the MeCab Python Binding [mecab-python-0.994.tar.gz]( http://code.google.com/p/mecab/downloads/list)

 - Extract the archive and open a command prompt in the extracted location

 - You will get an error if you were to simply build with the current setup.py as the Windows distribution of MeCab does not include the mecab-config program. Modify setup.py to contain:

    ```
#!/usr/bin/env python

    from distutils.core import setup,Extension

    setup(name = "mecab-python",
        version = '0.99',
        py_modules=["MeCab"],
        ext_modules = [
            Extension("_MeCab",
                ["MeCab_wrap.cxx",],
                include_dirs=[r"C:\Program Files\MeCab\sdk"],
                library_dirs=[r"C:\Program Files\MeCab\sdk"],
                libraries=['libmecab'])
                ])
    ```

 - Now run:
    ```
    $ python setup.py build
    $ python setup.py install
    ```

 - To check if everything went OK, run ```test.py```.

(Note: Windows cmd cannot display utf-8 characters correctly so you may want to run it in ```powershell_ise```)

References:
 - http://d.hatena.ne.jp/fuyumi3/20120113/1326383644
 - http://www.freia.jp/taka/blog/759/
 - http://d.hatena.ne.jp/mahan/20120618/13R40040589
 - http://triplepulu.web.fc2.com/mecab.html
 - http://www.mathworks.com.au/support/solutions/en/data/1-6IJJ3L/index.html?solution=1-6IJJ3L


