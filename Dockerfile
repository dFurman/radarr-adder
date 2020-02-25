FROM python
WORKDIR /app
COPY ./src/requirements.txt ./requirements.txt
RUN pip install -r requirements.txt
COPY ./src/* ./
CMD python ./main.py
