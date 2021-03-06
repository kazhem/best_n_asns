import socket
import csv
import pyasn
import heapq
import time


def get_or_create_asn(asns, asn):
    """
    Gets asn data by asn or creates new dict in asns dictionary in format:
    {'relations': [], 'domains': [], 'weight': 0, }
    """
    return asns.get(asn, {'relations': [], 'domains': [], 'weight': 0, })


def get_asn_by_domain(asndb, domain):
    """
    Returns asn by given pyasn db class and domain
    """
    asn = ''
    try:
        ip = socket.gethostbyname(domain)  # Asume we take first given i
        asn, mask = asndb.lookup(ip)
    except socket.gaierror as e:
        # for production use logger is better
        pass
        # print(f"Error on domain {domain} - {e}")
    return asn


def fill_relations(relations_path):
    """
    Read relations and fill ASNs with numbers and relations

    Return dict in format {'<asn>': {'relations': ['asn1', 'asn2'...],
                                            'domains':[],
                                            'weight': int}}
    """
    print(f"Parsing {relations_path} for ASN relations")
    asns = {}  # autonomous system numbers
    with open(relations_path, "r") as f_obj:
        reader = csv.reader(f_obj)
        for row in reader:
            asn = row[0]
            related_asn = row[1]
            if asn and related_asn:  # not empty
                # Get existing asn or create new
                asn_data = get_or_create_asn(asns, asn)
                # if related_asn not in asn_data['relations']: 10x longer
                # relations are unique
                asn_data['relations'].append(related_asn)
                asn_data['weight'] += 1
                asns[asn] = asn_data
            else:  # if one of column is empty
                print("Invalid row:", row)

    return asns


def fill_domains(asns, ipasn_db_path, top_domains_path, n_domains):
    """
    Adds domains from alexa top N to ASNs 'domains'
    """
    print(f"Parsing {ipasn_db_path} and {top_domains_path} for ASN domains.")
    asndb = pyasn.pyasn(ipasn_db_path)
    with open(top_domains_path, "r") as f_obj:
        reader = csv.reader(f_obj)
        counter = 0
        for row in reader:
            if counter == n_domains:
                break

            domain = row[1]
            asn = str(get_asn_by_domain(asndb, domain))
            if asn:
                asn_data = get_or_create_asn(asns, asn)
                # domains are unique
                asn_data['domains'].append(domain)
                asn_data['weight'] += 1
                asns[asn] = asn_data
            counter += 1

            if counter % 1000 == 0:
                print(f"Parsed {counter} domains")


def get_best_asns(relations_path, top_domains_path, ipasn_db_path, n_best=10,
                  n_domains=1000):
    """
    Get best N ASNs according to its weight.
    Weight = number of relations + number of hosted domains
    """
    # Read relations and fill ASNs with numbers and relations
    start_time = time.time()
    asns = fill_relations(relations_path)  # ASNs data
    print("Parsing finshed. Total ASNs: %s; %s sec" % (
                                        len(asns),
                                        round(time.time() - start_time)))

    start_time = time.time()
    fill_domains(asns, ipasn_db_path, top_domains_path, n_domains)
    print("Parsing of domains finshed. %s sec" % (round(time.time() - start_time)))

    n_largest = heapq.nlargest(n_best, asns, key=lambda x: asns[x]['weight'])

    for i, asn in enumerate(n_largest):
        relations_len = len(asns[asn]['relations'])
        domains_len = len(asns[asn]['domains'])
        weight = asns[asn]['weight']
        print(f'{i+1}. AS {asn}:\n\trelations: {relations_len}\n\t'
              f'domains: {domains_len}\n\tweight: {weight}')


if __name__ == "__main__":
    # For production - config
    relations_path = 'data/relations.csv'
    top_1m_domains = 'data/top-1m.csv'  # http://s3.amazonaws.com/alexa-static/top-1m.csv.zip
    # ipasn_db fil generated by:
    # pyasn_util_download.py --latest
    # pyasn_util_convert.py --single <Downloaded RIB File> <ipasn_db_file_name>
    ipasn_db_path = 'data/ipasn_20190425.dat'  # ftp://archive.routeviews.org/datapath/YYYYMM/ribs/XXXX - latest
    n_best = 10
    n_domains = 10000
    get_best_asns(relations_path, top_1m_domains, ipasn_db_path, n_best,
                  n_domains)
