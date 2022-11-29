from difPy import dif
from PIL import Image
import sys, os, pytest, pathlib, shutil

target=os.getenv('TARGET', '/code')
wdir=os.getenv('WDIR', '/tmp/wdir')
if os.path.isdir(wdir): shutil.rmtree(wdir)

def scale(src, trg, width):
   '''
   Scaling the image to expected width. 

   @param src The source image file
   @param trg The output image file
   @param width The expected image width
   '''
   img=Image.open(src)
   img.thumbnail((width, width), Image.Resampling.LANCZOS)
   img.save(trg)

@pytest.fixture
def prepare():
   '''
   Preparing the testing sample images. Due to the docker images may be read-only, this 

   @param src The source folder/directory.
   @param trg The target folder/directory.
   '''
   images=['.jpg', '.gif', '.png']
   sampling=[2048, ]
   print('Copying sample image(s) to working dir...')
   pathlib.Path(wdir).mkdir(parents=True, exist_ok=True)
   expected=0
   for f in os.listdir(target):
      src=os.path.join(target, f)
      if not os.path.isfile(src): continue
      if not os.access(src, os.R_OK): continue
      fn, ext=os.path.splitext(f)
      if ext.lower() in images:
         expected+=1
         print('   copying file: {0} => {1}'.format(src, os.path.join(wdir, f)))
         shutil.copyfile(src, os.path.join(wdir, f))
         for r in sampling:
            trg=os.path.join(wdir, '{0}-{1}{2}'.format(fn, r, ext))
            print('      - saving thumbnail ({0}) as {1}'.format(r, trg))
            scale(src, trg, r)
   os.environ['EXPECTED']=str(expected)

def test_difpy(prepare):
   print('Target dir: {0}'.format(target))
   print('Working dir: {0}'.format(wdir))

   #######
   search=dif(wdir)
   print('>>> We found {0} result'.format(len(search.result)))
   for r in search.result:
      rst=search.result[r]
      print('>>> - image: {0} ({1})'.format(rst['filename'], rst['location']))
      for d in rst['duplicates']:
         print('>>>    - duplication: {0}'.format(d))
   assert int(os.getenv('EXPECTED'))==len(search.result)
