FROM python
WORKDIR /app
COPY ./src/requirements.txt ./requirements.txt
RUN pip install --upgrade pip && \
    pip install -r requirements.txt
COPY ./src/* ./
RUN chmod +x ./main.py
CMD python ./main.py
