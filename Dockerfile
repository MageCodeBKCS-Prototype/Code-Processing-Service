FROM python:3.11
WORKDIR /app
COPY Code-Processing-Service/requirements.txt requirements.txt
RUN pip3 install --upgrade pip
RUN pip3 install fastapi[all] flower
RUN pip3 install -r requirements.txt
COPY Code-Processing-Service/.env /app/.env
COPY Code-Processing-Service/src/ /app/src
COPY codeql/ /codeql
ENV PATH="/codeql:${PATH}"
EXPOSE 8000
