FROM docker.elastic.co/elasticsearch/elasticsearch:8.11.1

RUN elasticsearch-plugin install --batch https://github.com/medcl/elasticsearch-analysis-pinyin/releases/download/v8.11.0/elasticsearch-analysis-pinyin-8.11.0.zip
