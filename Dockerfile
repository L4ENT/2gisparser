FROM joyzoursky/python-chromedriver:3.7-alpine3.8-selenium

ENV PROJECT_ROOT=/usr/src/application \
    USR_LOCAL_BIN=/usr/local/bin

ENV PYTHONPATH=$PYTHONPATH:$PROJECT_ROOT

RUN pip install --upgrade pip

RUN mkdir $PROJECT_ROOT

WORKDIR $PROJECT_ROOT

COPY ./ $PROJECT_ROOT

COPY Pipfile $PROJECT_ROOT
COPY Pipfile.lock $PROJECT_ROOT

RUN pip install pipenv
RUN pipenv install --deploy --system

# Service scripts
RUN for i in $PROJECT_ROOT/scripts/*; do \
    sed -i 's/\r//' $i; \
    chmod +x $i; \
    done

ENV PATH=$PATH:$PROJECT_ROOT/scripts/
