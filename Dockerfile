FROM python:3.11
WORKDIR /app
COPY magecode-backend/requirements.txt requirements.txt
RUN pip3 install --upgrade pip
RUN pip3 install fastapi[all] flower
RUN pip3 install -r requirements.txt
COPY magecode-backend/.env /app/.env
COPY magecode-backend/src/ /app/src
COPY CodeQL/codeql/codeql/ /codeql
ENV PATH="/codeql:${PATH}"
EXPOSE 8000
