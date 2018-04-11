import shutil
import os
import base64
import re

import logging
logging.basicConfig(level = logging.DEBUG)
log = logging.getLogger(__name__)

import requests
from jinja2 import Environment, FileSystemLoader

def cleanup():
    log.debug('Cleaning public folder ...')
    shutil.rmtree('public', ignore_errors = True)
    shutil.copytree('site', 'public')

def generate_output(data):
    data.update(os.environ) # Expose env variables to template
    log.debug('Generating output ...')
    env = Environment(loader = FileSystemLoader('.'))
    template = env.get_template('site/index.html')
    template.stream(data).dump('public/index.html')

def load_data():
    url = f'https://{os.environ["SHOPIFY_SHOP_DOMAIN"]}.myshopify.com/api/graphql'
    json = { 'query' : '''
{
  shop {
    name
    products(first: 10) {
      edges {
        node {
          id
          title
          descriptionHtml
          images(first: 1) {
            edges {
              node {
                originalSrc
              }
            }
          }
        }
      }
    }
  }
}
    ''' }
    headers = {'X-Shopify-Storefront-Access-Token': os.environ['SHOPIFY_STOREFRONT_TOKEN']}

    response = requests.post(url = url, json = json, headers = headers)
    return response.json()['data']

def transform_products(data):
    '''
    Transform encoded ID back to integer to use it in https://github.com/Shopify/buy-button-js
    '''
    def transform_id(product):
        # decode base64 encoded string
        id = str(base64.b64decode(product['node']['id']))
        # ID in following format will get returned gid://shopify/Product/10072080975
        # use regex to extract the number
        id = int(re.findall('\d+', id)[0])
        product['node']['id'] = id
        return product
    products = list(map(transform_id, data['shop']['products']['edges']))
    data['shop']['products']['edges'] = products
    return data

cleanup()
data = load_data()
data = transform_products(data)
generate_output(data)
