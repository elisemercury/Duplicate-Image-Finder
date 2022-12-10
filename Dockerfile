from alpine:latest

RUN adduser -g "" -D -u 1000 difpy \
 && mkdir /difpy                   \
 && chown difpy:difpy /difpy       \
 && apk --no-cache add python3     \
                       py-pip      \
                       py3-numpy

COPY . /difpy
WORKDIR /difpy
USER difpy:difpy

RUN export PATH="/home/difpy/.local/bin:$PATH" \
 && pip3 install --user --upgrade pip          \
 && pip3 install --user -r requirements.txt    \
 && python3 setup.py sdist                     \
 && pip3 install --user dist/*

ENTRYPOINT ["/home/difpy/.local/bin/difpy"]
