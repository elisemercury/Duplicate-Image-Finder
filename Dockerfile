FROM python:3.10-alpine

LABEL maintainer='Kenosn Man <kenson.idv.hk@gmail.com>'
LABEL version='2.4.4'

RUN \
  echo ">>> Installing the dependencies ..." && \
  apk add --no-cache qt5-qtbase-dev qt5-qtdeclarative-dev qt5-qtwebsockets-dev qt5-qtwebchannel-dev qt5-qtwebengine-dev qt5-qtsvg-dev qt5-qtconnectivity-dev qt5-qtcharts-dev \
                     qt5-qtvirtualkeyboard-dev qt5-qtlocation-dev qt5-qttools-dev qt5-qtquickcontrols2-dev qt5-qtwayland-dev qt5-qtxmlpatterns-dev qt5-qtx11extras-dev qt5-qtserialport-dev \
                     qt5-qtsensors-dev qt5-qtmultimedia-dev qt5-qtspeech-dev qt5-qtremoteobjects-dev qt5-qtscript-dev qt5-qtimageformats qt5-qttranslations qt5-qtgraphicaleffects \
                     bash bash-doc bash-completion musl-dev gfortran gdb g++ make automake subversion python3-dev openblas openblas-dev && \
  echo ">>> Installing the difPy ..." && \
  pip install --no-cache-dir difPy && \
  echo ">>> Finishing ..." && \
  adduser -S theuser

USER theuser
CMD ["bash"]
