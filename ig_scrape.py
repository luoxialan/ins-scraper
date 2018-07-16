# coding : UTF-8
import sys
reload(sys)  
sys.setdefaultencoding('utf8')

import json
import requests
from lxml import etree
import re
import md5

IG_URL = "https://www.instagram.com"
IG_ACCOUNT_URL = "https://www.instagram.com/{}/"
IG_POST_URL = "https://www.instagram.com/p/{}/?taken-by={}" # https://www.instagram.com/p/{shortcode}?taken-by={user_name}
IG_POST_QUERY_ENDPOINT = "/graphql/query/?query_hash={}&variables={}"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36"
HEADERS = {
    "Origin": IG_URL,
    "User-Agent": USER_AGENT,
    "Host": "www.instagram.com",
    "x-requested-with": "XMLHttpRequest",
    'Connection': 'keep-alive'
}
IG_ACCOUNTS = [
    "9gag", "barked", "meowed", "voyaged"
]
SCRAPE_PAGE_COUNT = 6
REMOVED_KEYS = [
   "query_js", "query_hash", "csrftoken", "page_info", "rhx_gis"
]

ig_account = "https://www.instagram.com/9gag/"

def get_query_hash(query_js):
    js_url = IG_URL + query_js
    res = requests.get(js_url)
    text = res.text
    query_hash = ""
    for query_id in re.findall("(?<=r.pagination},queryId:\")[0-9A-z]+", text):
        query_hash =  query_id
    return query_hash

def get_fisrt_page(ig_account):
    ig_account_data = {}
    ig_first_page = {}

    # 1. call the instagram acount home page
    session = requests.session()
    session.headers.update(HEADERS)
    res = session.get(ig_account)
    cookies = session.cookies.get_dict()
    html = etree.HTML(res.content.decode())
    
    # 2. process the html page
    # 2.1 get the ig data object
    insta_data = html.xpath('''//script[@type="text/javascript"]''')[3].text.replace('window._sharedData = ','').strip()[:-1]
    dic = json.loads(insta_data, encoding='utf-8')
    user_data = dic['entry_data']['ProfilePage'][0]['graphql']['user']
    data = dic['entry_data']['ProfilePage'][0]['graphql']['user']['edge_owner_to_timeline_media']

    # 2.2 get the query data
    ig_account_data['user_id'] = user_data['id']
    ig_account_data['user_name'] = user_data['username'] 
    ig_account_data['user_biography'] = user_data['biography'] 
    ig_account_data['user_followby'] = user_data['edge_followed_by']['count'] 
    ig_account_data['user_follow'] = user_data['edge_follow']['count']
    ig_account_data['user_profile_pic'] = {}
    ig_account_data['user_profile_pic']['url'] = user_data['profile_pic_url']
    ig_account_data['user_profile_pic']['hd_url'] = user_data['profile_pic_url_hd']
    ig_account_data['rhx_gis'] = dic['rhx_gis'] 
    ig_account_data['csrftoken'] = cookies.get("csrftoken")
    js_src = html.xpath('''//script[@type="text/javascript"]/@src''')
    ig_account_data['query_js'] = "" 
    for js in js_src:
        if "ProfilePageContainer.js" in js: 
            ig_account_data['query_js'] = js
    ig_account_data['query_hash'] = get_query_hash(ig_account_data['query_js'])

    # 2.3 get the posts data
    nodes = data['edges']
    post_list = process_post_data(nodes, ig_account_data['user_name'])
    ig_first_page['posts'] = post_list
    ig_first_page['page_info'] = data['page_info']

    return ig_account_data, ig_first_page

def process_post_data(posts, user_name):
    post_list = []
    for post in posts:
        post = post['node']
        p = {}
        p["post_id"] = post['id']
        p["post_shortcode"] = post['shortcode']
        p["post_url"] = IG_POST_URL.format(p["post_shortcode"], user_name)
        p["thumbnail_url"] = post['thumbnail_src']
        p["post_type"] = post['__typename']
        p["post_text"] = post['edge_media_to_caption']['edges'][0]['node']['text']
        p["hashtag"] = get_hashtag(p["post_text"])
        p["post_is_video"] = post['is_video']
        p["post_create_at"] = post['taken_at_timestamp']
        p["post_comment"] = post['edge_media_to_comment']['count']
        # p["post_like"] = post['node']['edge_liked_by']['count']
        p["post_like"] =  post['edge_media_preview_like']['count']
        p["post_view_count"] = 0
        if p["post_is_video"] is True:
            p["post_view_count"] = post['video_view_count']
        post_list.append(p)
    return post_list

def get_params(user_id, end_cursor):
    return '{{"id":"{}","first":12,"after":"{}"}}'.format(user_id, end_cursor)

def get_ig_gis(rhx_gis, params):
    return md5.new(rhx_gis + ":" + params).hexdigest()

def make_headers(ig_gis):
    return {
        "x-instagram-gis": ig_gis,
        "x-requested-with": "XMLHttpRequest",
        "user-agent": USER_AGENT
    }

def load_more(ig_account_meta):
    more = []
    page_info = {
        "has_next_page": False,
        "end_cursor": ""
    }
    params = get_params(ig_account_meta['user_id'], ig_account_meta['page_info']['end_cursor'])
    query_hash = get_query_hash(ig_account_meta['query_js'])
    url = IG_URL+IG_POST_QUERY_ENDPOINT.format(query_hash, params)
    ig_gis = get_ig_gis(ig_account_meta['rhx_gis'], params)
    update_headers = make_headers(ig_gis)
    res = requests.get(url, headers = update_headers)
    
    dic = json.loads(res.content.decode(), encoding='utf-8')
    data = dic['data']['user']['edge_owner_to_timeline_media'] 
    page_info = data['page_info']   
    nodes = data['edges']
    more = process_post_data(nodes, ig_account_meta['user_name'])
    return more, page_info

def scrape_page(ig_account):
    ig_meta_data = {}
    page_data = {}
    ig_meta_data, page_data = get_fisrt_page(ig_account)
    ig_meta_data['page_info'] = page_data['page_info']
    ig_meta_data['posts'] = page_data['posts']
    page_count = 1
    while page_count < SCRAPE_PAGE_COUNT and ig_meta_data['page_info']['has_next_page'] == True:
        page_info = {}
        more = []
        more, page_info = load_more(ig_meta_data)
        ig_meta_data['page_info'] = page_info
        ig_meta_data['posts'].append(more) 
        page_count += 1
    
    for k in REMOVED_KEYS:
        ig_meta_data = remove_key(ig_meta_data, k)
    return ig_meta_data       

def get_hashtag(post_text):
    hash_tags = []
    tags_strs = post_text.split(' ')
    tags = []
    for tag_str in tags_strs:
        if "#" in tag_str: 
            tags.append(tag_str)
    for tag in tags:
        t = tag.split("#")
        l = len(t)
        if l > 0:
            hash_tags.append("#"+t[l-1])
    return hash_tags

def remove_key(d, k):
    r = dict(d)
    del r[k]
    return r

if __name__=='__main__':
    ig_accounts_data = []
    for ig_account in IG_ACCOUNTS:
        ig_home_url = IG_ACCOUNT_URL.format(ig_account)
        ig_meta_data = scrape_page(ig_home_url)
        ig_accounts_data.append(ig_meta_data)
    ig_accounts_data = json.dumps(ig_accounts_data)
    print ig_accounts_data
