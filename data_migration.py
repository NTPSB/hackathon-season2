from xml.etree import ElementTree
import pandas as pd
import matplotlib.pyplot as plt
import csv, sqlite3
import argparse
from datetime import datetime
import numpy as np
    

field_name = ['EMPID', 'PASSPORT', 'FIRSTNAME', 'LASTNAME', 'GENDER', 'BIRTHDAY', 'NATIONALITY', 'HIRED', 'DEPT', 'POSITION', 'STATUS', 'REGION']


def xml2csv(xml_file, csv_file):
    tree = ElementTree.parse(xml_file)
    root = tree.getroot()
    data_lst = clean_data(root)

    with open(csv_file, 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames = field_name)
        writer.writeheader()
        writer.writerows(data_lst)

def cal_age(date):
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
            cal_age(datetime.strptime(record.find('HIRED').text, '%d-%m-%Y').date()) > 3:

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

def visualize(csv_file):
    df = pd.read_csv(csv_file)
    figure, axis = plt.subplots(2, 2)
    data = [len(df[df['GENDER']==0]), len(df[df['GENDER']==1])]
    axis[0, 0].pie(data, labels = ["Male", "Female"])
    axis[0, 0].set_title("Gender")

    region = df['REGION'].value_counts().rename_axis('region').reset_index(name='counts')
    axis[0, 1].pie(region['counts'], labels=region['region'])
    axis[0, 1].set_title("Region")

    df['WORK_EXP'] = df.apply(lambda x: cal_age(datetime.strptime(x['HIRED'], '%d-%m-%Y').date()), axis=1)
    axis[1, 0].barh(df['FIRSTNAME'], df['WORK_EXP'], color ='maroon')
    axis[1, 0].invert_yaxis()
    axis[1, 0].set_xlabel('Years')
    axis[1, 0].set_title('Work Experience')

    df_gender_count = df.groupby(["GENDER", "POSITION"]).size().reset_index()
    df_male = df_gender_count[df_gender_count['GENDER'] == 0]
    df_female = df_gender_count[df_gender_count['GENDER'] == 1]
    ind = np.arange(3)
    width = 0.35
    p1 = axis[1, 1].bar(ind, tuple(df_male[0].values), width)
    p2 = axis[1, 1].bar(ind, tuple(df_female[0].values), width, bottom = tuple(df_male[0].values))
    axis[1, 1].set_ylabel('Contribution')
    axis[1, 1].set_title('Contribution by the teams')
    axis[1, 1].set_xticks(ind)
    axis[1, 1].set_xticklabels(['Airhostess', 'Pilot', 'Steward'])
    axis[1, 1].legend((p1[0], p2[0]), ('Male', 'Female'))
    plt.show()

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
    
    if args.action == 'visualize':
        visualize(csv_file=args.csv)
