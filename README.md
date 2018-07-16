# ins-scraper

This script scrape the 4 instagram account below which include user account data and posts data.

1. [@9gag](https://www.instagram.com/9gag/)  
2. [@barked](https://www.instagram.com/barked/)
3. [@meowed](https://www.instagram.com/meowed/)
4. [@voyaged](https://www.instagram.com/voyaged/)

Usage
-----
To run the script and get the result

```bash
$ python ig_scrape.py >> result.json
```

Post meta data example

```bash
  {
    "post_comment":376,
    "post_text":"Not sure if everyone is busy or I have no friends\n-\n#9gag",
    "post_create_at":1531695963,
    "post_like":77294,
    "post_view_count":0,
    "post_url":"https://www.instagram.com/p/BlRScK3FaZq/?taken-by=9gag",
    "post_id":"1824320424705893994",
    "thumbnail_url":"https://instagram.fhkg3-1.fna.fbcdn.net/vp/f94d5755284f1f4a207b7114f5aaa7de/5BC735D0/t51.2885-15/sh0.08/e35/s640x640/36800497_225756328059887_4684911319583817728_n.jpg",
    "post_type":"GraphImage",
    "hashtag":[
      "#9gag"
    ],
    "post_is_video":false,
    "post_shortcode":"BlRScK3FaZq"
}
```
