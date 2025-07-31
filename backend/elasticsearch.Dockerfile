FROM docker.elastic.co/elasticsearch/elasticsearch:8.11.1

RUN elasticsearch-plugin install --batch https://release.infinilabs.com/analysis-pinyin/stable/elasticsearch-analysis-pinyin-9.1.0.zip
