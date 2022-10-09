from xml.etree import ElementTree
import pandas as pd
import matplotlib.pyplot as plt
import csv, sqlite3
import argparse
from datetime import datetime
    

field_name = ['EMPID', 'PASSPORT', 'FIRSTNAME', 'LASTNAME', 'GENDER', 'BIRTHDAY', 'NATIONALITY', 'HIRED', 'DEPT', 'POSITION', 'STATUS', 'REGION']


def xml2csv(xml_file, csv_file):
    tree = ElementTree.parse(xml_file)
    root = tree.getroot()
    data_lst = clean_data(root)

    with open(csv_file, 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames = field_name)
        writer.writeheader()
        writer.writerows(data_lst)

def cal_work_exp(date):
    today = date.today()
    work_exp = today.year - date.year - ((today.month, today.day) < (date.month, date.day))
    return work_exp


def clean_data(records):
    data_return = []
    existed_empid = []
    existed_passport = []
    for record in records:
        if record.find('POSITION').text in ['Airhostess', 'Pilot', 'Steward'] and\
            record.find('STATUS').text == '1' and\
            record.find('EMPID').text not in existed_empid and\
            record.find('PASSPORT').text not in existed_passport and\
            cal_work_exp(datetime.strptime(record.find('HIRED').text, '%d-%m-%Y').date()) > 3:

            data_return.append({el.tag: el.text for el in record})
            existed_empid.append(record.find('EMPID').text)
            existed_passport.append(record.find('PASSPORT').text)
    return data_return

def insert2sqlite(csv_file, database_name, table_name):
    con = sqlite3.connect(database_name)
    cursor = con.cursor()

    first = True
    with open (csv_file, 'r') as f:
        reader = csv.reader(f)
        columns = next(reader)
        columns = [h.strip() for h in columns]
        if first:
            sql = 'CREATE TABLE IF NOT EXISTS {} ({})'.format(table_name, ', '.join(['%s text'%column for column in columns]))
            cursor.execute(sql)
            first = False

        query = 'insert into {}({}) values ({})'
        query = query.format(table_name, ','.join(columns), ','.join('?' * len(columns)))
        cursor = con.cursor()
        for row in reader:
            cursor.execute(query, row)
        con.commit()
        con.close()

# def visualize():
#     df = pd.read_csv("test4.csv")
#     print(len(df[df['GENDER']==0]))
#     print(len(df[df['GENDER']==1]))
#     import numpy as np
#     t=np.arange(0, 5, 0.2)

#     # pie chart: gender
#     plt.subplot(121)
#     data = [len(df[df['GENDER']==0]), len(df[df['GENDER']==1])]
#     plt.pie(data, labels = ["Male", "Female"])
#     plt.xlabel("Gender")

#     plt.subplot(122)
#     region = df['REGION'].value_counts().rename_axis('region').reset_index(name='counts')
#     plt.pie(region['counts'], labels=region['region'])
#     plt.xlabel("Graph 1")
#     plt.show()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-action", "--action", help="action type")
    parser.add_argument("-xml", "--xml", help="xml file", default='data-devclub-1.xml')
    parser.add_argument("-csv", "--csv", help="csv file", default='data-devclub-1.csv')
    parser.add_argument("-db", "--db", help="database name", default='data-devclub.sqlite')
    parser.add_argument("-table", "--table", help="table name", default='Emp')
    args = parser.parse_args()
    if args.action == 'xml2csv':
        xml2csv(xml_file=args.xml, csv_file=args.csv)
    
    if args.action == 'csv2sqlite':
        insert2sqlite(csv_file=args.csv, database_name=args.db, table_name=args.table)
