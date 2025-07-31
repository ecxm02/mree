FROM docker.elastic.co/elasticsearch/elasticsearch:8.11.1

RUN elasticsearch-plugin install --batch https://release.infinilabs.com/analysis-pinyin/stable/elasticsearch-analysis-pinyin-8.11.1.zip
