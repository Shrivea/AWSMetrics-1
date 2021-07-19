import requests
from bs4 import BeautifulSoup
import re
import yaml
import csv
import os

UNITS_ = 'Units:'
VALID_STATISTICS_ = 'Valid statistics:'
LATENCY_VALUES = ['minimum', 'maximum', 'p50', 'p90', 'p95', 'p99', 'p99.99']
CODE_MAP = {

    'Read Throughput (IOPS)': 'read_throughput(iops)',
    'Write Throughput (IOPS)': 'write_throughput(iops)',
    'Avg Read Latency (ms/Operation)':'avg_read_latency_(ms/operation)',
    'Read Bandwidth (KiB/s)':'read_bandwith_(kib/s)',
    'Write Bandwidth (KiB/s)':'write_bandwith_(kib/s)',
    'Avg Write Latency (ms/Operation)':'avg_write_latency_(ms/operation)',
    'Avg Queue Length (Operations)':'aws_queue_length_(operations)',
    '% Time Spent Idle':'%_time_spent_idle',
    'Avg Read Size (KiB/Operation)':'avg_read_size_(kib/operation)',
    'Avg Write Size (KiB/Operation)':'avg_write_size_(kib/operation)'


}

METRIC_HEADERS = ["metric_name", "metric_type", "interval", "unit_name", "per_unit_name", "description", "orientation",
                  "integration", "short_name", ]
YAML_FILE = "AWS.EBS.yaml"
CSV_FILE = "AWS.EBS.csv"


class AWSEBSExtractor:
    def __init__(self, url):
        self.url = url
        self.content = ""
        self.aws_dict = {}
        self.aws_list = []

    def load_page(self):
        page = requests.get(self.url)
        if page.status_code == 200:
            self.content = page.content

    def get_content(self):
        return self.content

    def get_metric_name(self, col):
        original_metric_name = col.text.strip()
        metric_name_snake_case = self.snake_case(original_metric_name)
        metric_name = metric_name_snake_case
        if metric_name.startswith('c_p_u_'):
            metric_name = metric_name.replace('c_p_u_', 'cpu_')
        return metric_name

    # @staticmethod
    # def get_metric_description(section):

    def process_content(self):
        soup = BeautifulSoup(self.content, 'html.parser')
        main_content = soup.findAll('table')
        rows = main_content[0].findAll('tr')
        self.aws_dict = {'type': 'ebs', 'keys': []}

        metric_name = ''
        metric_desc = ''
        metric_units = ''
        for table in rows[1:]:
            cols = table.findAll('td')
            col = cols[0]
            original_metric_name = col.text.strip()
            metric_name = 'aws.ebs.' + self.snake_case(col.text.strip())
            if original_metric_name in CODE_MAP.keys():
                metric_name = CODE_MAP[original_metric_name]
            # if metric_name ==
            self.aws_dict['keys'].append(
                {'name': metric_name, 'alias': 'dimension_' + original_metric_name})
            # print(metric_name)
            coltwo = cols[1]
            sections = coltwo.findChildren('p')
            if sections and len(sections) > 0:
                idx = 0
                for i in sections:
                    descriptions = i.findAll(text=True)
                    var1 = ' '.join(descriptions)
                    var1 = var1.replace('\n', '')
                    var2 = ' '.join(var1.split())
                    # print(var2)
                    if idx == 0 and var2:
                        metric_desc = var2
                        # print(metric_desc)
                    elif var2.startswith('Units'):
                        metric_units = var2.replace('Units: ', '')
                        # print(metric_units)
                        if 'Count' not in metric_units:
                            metric_units = 'guage'
                        else:
                            metric_units = 'count'
                    idx = idx + 1
                self.add_to_list(self.aws_list, metric_name, metric_units, metric_desc)
                self.add_to_list(self.aws_list, metric_name + "_min", metric_units, metric_desc + "_min")
                self.add_to_list(self.aws_list, metric_name + "_max", metric_units, metric_desc + "_max")
                self.add_to_list(self.aws_list, metric_name + "_avg", metric_units, metric_desc + "_avg")

        rowone = main_content[1].findAll('tr')

        for x in rowone[1:]:
            metricnameone = ''
            metricdescone = ''
            colone = x.findAll('td')
            cole = colone[0]
            ogmetricname = cole.text.strip()
            metricnameone = 'aws.ebs.' + self.snake_case(cole.text.strip())
            self.aws_dict['keys'].append(
                {'name': metricnameone, 'alias': 'dimension_' + ogmetricname})
            # print(metricnameone)
            coles = colone[1]
            sectionone = coles.findChildren('p')
            if sectionone:
                for r in sectionone:
                    descritwo = coles.findAll(text=True)
                    var10 = ' '.join(descritwo)
                    var10 = var10.replace('\n', '')
                    var16 = ' '.join(var10.split())
                    metricdescone = var16
                self.add_to_list(self.aws_list, metricnameone, "", metricdescone)
                self.add_to_list(self.aws_list, metricnameone + "_min", "", metricdescone + "_min")
                self.add_to_list(self.aws_list, metricnameone + "_max", "", metricdescone + "_max")
                self.add_to_list(self.aws_list, metricnameone + "_avg", "", metricdescone + "_avg")
        rowtwo = main_content[2].findAll('tr')
        for j in rowtwo[1:]:
            metricnameoneone = ''
            metricdesconeone = ''
            coloneone = j.findAll('td')
            coless = coloneone[0]
            ogonemetricname = coless.text.strip()
            metricnameoneone = 'aws.ebs.' + self.snake_case(coless.text.strip())
            if ogonemetricname in CODE_MAP.keys():
                metricnameoneone = 'aws.ebs.' + CODE_MAP[ogonemetricname]
            self.aws_dict['keys'].append(
                {'name': metricnameoneone,'alias': 'dimension_' + ogonemetricname})
            # print(metricnameone)
            colesthree = coloneone[1]
            sectiononetwo = colesthree.findChildren('p')
            descriptionsone = colesthree.findAll(text=True)
            var5 = ' '.join(descriptionsone)
            var5 = var5.replace('\n', '')
            var6 = ' '.join(var5.split())
            metricdesconeone = var6
            self.add_to_list(self.aws_list, metricnameoneone, "", metricdesconeone)
            self.add_to_list(self.aws_list, metricnameoneone + "_min", "", metricdesconeone + "_min")
            self.add_to_list(self.aws_list, metricnameoneone + "_max", "", metricdesconeone + "_max")
            self.add_to_list(self.aws_list, metricnameoneone + "_avg", "", metricdesconeone + "_avg")

    def generate_csv(self):
        path1 = './CSV_FOLDER'
        os.chdir(path1)
        with open(CSV_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(METRIC_HEADERS)
            writer.writerows(self.aws_list)
        os.chdir('..')

    def generate_yaml(self):
        path1 = './YAML_FOLDER'
        os.chdir(path1)
        with open(YAML_FILE, 'w') as outfile:
            yaml.dump([self.aws_dict], outfile, default_flow_style=False)
        os.chdir('..')

    @staticmethod
    def add_to_list(aws_list, metric_name, metric_type, description):
      #  print(metric_name, '||', metric_type, "||", description)
        aws_list.append([metric_name, metric_type, "", "", "", description, "", "ebs", ""])

    @staticmethod
    def snake_case(input_string):
        if input_string:
            return re.sub(r'(?<!^)(?=[A-Z])', '_', input_string).lower()
        else:
            return input_string


if __name__ == "__main__":
    extractor = AWSEBSExtractor('https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using_cloudwatch_ebs.html')
    extractor.load_page()
    extractor.process_content()
    extractor.generate_yaml()
    extractor.generate_csv()
