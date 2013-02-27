'''
Created on Feb 13, 2013

@author: ozbolt
'''

APIKEY_RT = "zj3y2qsm6q2t5pef2spv7bnd"

import urllib.request, urllib.error
from urllib.parse import urlparse
from Base import Movie, Release
import datetime
import bs4
from lxml import etree
from Tools import *
from time import time

import threading

########################
###  Config Folders  ###
########################

TORRENT_WEBSITES = "torrentSites.txt"
RELEASERS = "releasers.txt"
URLS_WAIT_TIME = "../config/urlsWait.json"
URLS_LAST_OPENED = "../config/urlsLast.json"

class Fetcher(threading.Thread):
    
    keywords = {"query": "",
                "movie": None, 
                "else": None} 
    
    def run(self):
        query = self.keywords["query"]
        
        if query == "movieDetails":
            self.queryOmdbApiFull(self.keywords["movie"])
        elif query == "movieUpdate":
            self.queryOmdbApiQuickUpdate(self.keywords["movie"])
        elif query == "upcoming":
            return self.queryRottenTomatoList("U")
        elif query == "boxOffice":
            return self.queryRottenTomatoList("B")
        elif query == "dvdReleases":
            return self.queryRottenTomatoList("D")
        elif query == "trailer":
            self.queryYoutubeTrailer(self.keywords["movie"])
        elif query == "dvdrip":
            self.queryTorrentz(self.keywords["movie"])
        
            
        #{"torrentz.eu": 0.1}
            
    def scrape(self, someurl):
        
        
        print("\tscraping: " + someurl)
        
        permitted = False
        while not permitted:
            netloc = urlparse(someurl).netloc
            now = time()
            
            f = open(URLS_LAST_OPENED, "r")
            lastOpened = json.load(f)
            f.close()
            
            #print("decoding1:", lastOpened)
            
            if netloc in lastOpened:
                lastTime = lastOpened[netloc]
            else:
                lastTime = 0
            
            f = open(URLS_WAIT_TIME, "r")
            waitTimes = json.load(f)
            f.close()
            
            #print("decoding2", waitTimes)
            
            if netloc in waitTimes:
                waitTime = waitTimes[netloc]
            else:
                waitTimes[netloc] = 0.1
                f = open(URLS_WAIT_TIME, "w")
                json.dump(waitTimes, f)
                f.close()
                waitTime = 0.1

                    
            if now - lastTime > waitTime:
                f = open(URLS_LAST_OPENED, "r")
                lastOpened = json.load(f)
                lastOpened[netloc] = now
                #print("all good, dumping: ", lastOpened)
                f = open(URLS_LAST_OPENED, "w")
                json.dump(lastOpened, f)
                f.close()
                break
            
            try:
                print("sleeping...WT")
                time.sleep(waitTime)
                print("awake!")
            except:
                print("sleeping...")
                time.sleep(0.1)
                print("awake!")
        
        html = ""
        i = 0
        while html == "" and i<2:
            i = i + 1
            try:            
                response = urllib.request.urlopen(someurl)
                
                charset = response.info()['Content-Type']
                index = charset.find("charset=")
                
                if index < 0:
                    charset = "utf8"
                else:
                    charset = charset[index+8:]
                    if ";" in charset:
                        charset = charset[0:charset.find(";")]
                
                html = response.read().decode(charset)
    
            except urllib.error.HTTPError as e:
                print(e.code)
                print(e.read())
            except UnicodeDecodeError as e:
                print("decoding failed!")
        
        if not html:
            print("not scraped: ", someurl)
        return html
            
    def _queryOmdbApiHelper(self, title = "", id_IMDB = -1, year = -1):
        url = "http://www.omdbapi.com/?plot=full&"
        
        if id_IMDB != -1:
            i = "tt0000000"[:9 - len('%d' % id_IMDB)] + str(id_IMDB)
            url += "i=" + i + "&"
        elif year != -1:
            url += "y=" + str(year) + "&"
        url += "t=" + title.lower().replace(" ", "+")

        jsonData = self.scrape(url)
        data = json.loads(jsonData)
                
        if data["Response"] == "False":
            raise 
        return data
    
    def queryOmdbApiFull(self, movie):
        
        if movie.id_IMDB != -1:
            data = self._queryOmdbApiHelper(id_IMDB = movie.id_IMDB)
        else:
            data = self._queryOmdbApiHelper(title = movie.title, year = movie.year)
        
        try:
            movie.title = data["Title"]
            movie.year = data["Year"]
            movie.IMDB_rating = float(data["imdbRating"])
            movie.IMDB_votes = int(data["imdbVotes"].replace(",", ""))
            movie.id_IMDB = int(data["imdbID"][2:])
            movie.director = data["Director"]
            movie.actor = data["Actors"].split(", ")
            movie.genre = data["Genre"].split(", ")
            movie.plot = data["Plot"]
            movie.dateRelease = datetime.datetime.strptime(data["Released"], "%d %b %Y" )
            runtime = data["Runtime"].split(" ")
            print(runtime)
            
            if "h" in runtime:
                h = int(runtime[0])
                m = 0
                if "m" in runtime or "min" in runtime:
                    m = int(runtime[2])
            else:
                h = 0
                m = int(runtime[0])
            movie.runTime = h*60 + m
            
            if data["Poster"] != "N/A":
                movie.linkPhoto = data["Poster"]
            else:
                movie.linkPhoto = ""
             
        except:
            print("Update data not full")
    
    def queryOmdbApiQuickUpdate(self, movie):
        '''
        Updating:
        - imdbRating
        - imdbVotes
        '''
        
        newData = self._queryOmdbApiHelper(id_IMDB = movie.id_IMDB)
        
        try:
            rating = newData["imdbRating"]
            votes = newData["imdbVotes"].replace(",", "")
            if rating == "N/A":
                rating = "0"
            if votes == "N/A":
                votes = "0"
                        
            movie.IMDB_rating = float(rating)
            movie.IMDB_votes = int(votes)
        except:
            print("Update data not avaliable")
        
    def queryRottenTomatoList(self, listType, resoultLen = 20, country = "us"):
        
        url = "http://api.rottentomatoes.com/api/public/v1.0/lists"
        if listType == "U":
            url += "/movies/upcoming.json?"
        elif listType == "B":
            url += "/movies/box_office.json?"
        elif listType == "D":
            url += "/dvds/new_releases.json?"
        
        url += "page=1&"
        url += "page_limit=" + str(resoultLen)
        url += "&country=" + country
        url += "&apikey=" + APIKEY_RT
        
        response = self.scrape(url)
        
        data = json.loads(response)
        
        movies = []
        i = 1
        for movie in data["movies"]:
            try:
                movie["alternate_ids"]["imdb"]
            except:
                continue
            m = Movie()
            m.id_IMDB = int(movie["alternate_ids"]["imdb"])
            m.plot = movie["synopsis"]
            m.title = movie["title"]
            m.year = movie["year"]
            #if "theater" in movie["release_dates"]:
            #    m.dateRelease = datetime.datetime.strptime(movie["release_dates"]["theater"], "%Y-%m-%d")
            m.linkPhoto = movie["posters"]["original"]
            #m.runTime = movie["runtime"]
            m.id_RT = movie["id"]
            m.boxOffice = i
            i = i+1
                        
            movies.append(m)

        #for m in movies:
            #print(m)
            
        return movies
    
    def queryRottenTomatoMovie(self, movie):
        url = "http://api.rottentomatoes.com/api/public/v1.0/movies.json?q="
        url += movie.title.replace(" ", "+") + "%20" + movie.year
        url += "&page_limit=3&apikey=zj3y2qsm6q2t5pef2spv7bnd"
        
        returned = self.scrape(url)
        returned = json.loads(returned)
        
        #print(json.dumps(returned, indent = "\t"))
        
        if returned["total"] == 0:
            return
        
        for res in returned["movies"]:
            
            if strCmp(movie.title, res["title"]) < 0.95 or int(movie.year) != res["year"]:
                continue
            
            print("through")
            
            movie.id_RT = res["id"]
                        
            if "critics_score" in res["ratings"]:
                movie.rt_critict = res["ratings"]["critics_score"]
            if "audience_score" in res["ratings"]:
                movie.rt_audience = res["ratings"]["audience_score"]
            if "poster" in res:
                if "original" in res["poster"]:
                    movie.linkPhoto = res["poster"]["original"]
                       
            if movie.dateRelease == None and "theater" in res["release_dates"]:
                movie.dateRelease = datetime.datetime.strptime(res["release_dates"]["theater"], "%Y-%m-%d")
            
            if movie.runTime == -1 and "runtime" in res:
                movie.runTime = res["runtime"]
            
            return       
    
    def _queryYoutubeTrailerHelper(self, title, year, maxResoults = 5, official = True, HD = True):
        if official: 
            query = title + " official trailer" 
        else:
            query = title + " trailer"
        
        url = "http://gdata.youtube.com/feeds/api/videos?v=2&q=" + query.replace(" ", "+") + "&max-results=" + str(maxResoults)
        if HD:
            url += "&hd=true"
        
        xml = self.scrape(url)
        xml = xml[xml.find(">")+1:] #removing first not well-formatted tag, leaving well formatted xml
        
        root = etree.fromstring(xml)
        
        entries = root.findall("{http://www.w3.org/2005/Atom}entry")
        
        ytmovies = []
        for entrie in entries:
            tmpMovie = {}
            tmpT = entrie.find("{http://www.w3.org/2005/Atom}title").text
            tmpMovie["cmp"] = trailerCheck(query, tmpT, year)
            if tmpMovie["cmp"] < 0.4:
                continue
            group = entrie.find("{http://search.yahoo.com/mrss/}group")
            try:
                dur = int(group.find("{http://search.yahoo.com/mrss/}content").get("duration"))
                if 60 > dur or dur > 500:
                    continue
            except:
                pass
            tmpMovie["id"] = group.find("{http://gdata.youtube.com/schemas/2007}videoid").text
            ytmovies.append(tmpMovie)

        
        if ytmovies == []:
            return None
        
        mov = 0
        for i in range(len(ytmovies)):
            if i==0:
                continue
            if ytmovies[i]["cmp"] > ytmovies[mov]["cmp"] + 0.05:
                mov = i
        
        return ytmovies[mov]["id"]
    
    def queryYoutubeTrailer(self, movie):
        trailer = self._queryYoutubeTrailerHelper(movie.title, movie.year)
        if not trailer:
            trailer = self._queryYoutubeTrailerHelper(movie.title, movie.year, HD = False)
        if not trailer:
            trailer = self._queryYoutubeTrailerHelper(movie.title, movie.year, official = False, HD = False)
        movie.linkTrailer = trailer
  
    def _queryTorrentzHelper(self, data, minSeeds = 3, noOfResoults = 5):
        '''
        In data:
        - "title"
        - "year"
        - "typ" (0,1)
        '''
        
        url = "http://torrentz.eu/feed?q="
        if "title" in data:
            url = url + data["title"].replace(" ", "+") + "+"
        if "year" in data:
            url = url + str(data["year"]) + "+"
            
        if data["typ"] == 0:
            mIn, mAx = 600, 1500
            toTry = ["dvdrip", "webrip"]
        elif data["typ"] == 1:
            mIn, mAx = 1000, 10000
            toTry = ["1080p", "brrip", "bdrip", "720p"]
        else:
            raise
        
        releases = []
        
        for rls in toTry:
            tmpUrl = url + rls
            xml = self.scrape(tmpUrl)
            root = etree.fromstring(xml)[0]
            i = 0
            
            print("searching:", tmpUrl)
            
            while len(releases) < noOfResoults and i < len(root):
                if root[i].tag != "item":
                    i = i + 1
                    continue
                
                tmpRelease = {}
                bad = False
                
                for child in root[i]:
                    if child.tag == "description":
                        description = re.split('[a-z]+: ', child.text, flags=re.IGNORECASE)
                        tmpRelease["seeds"] = int(description[2].replace(",", ""))
                        tmpRelease["size"] = int(description[1][0:-3])
                        if "KB" in description[1] or len(description[1]) < 6 or tmpRelease["seeds"] < minSeeds or not (mIn < tmpRelease["size"] < mAx):
                            bad = True
                            break
                        else:
                            tmpRelease["peers"] = int(description[3].replace(",", ""))
                            tmpRelease["hash"] = description[4]
                    elif child.tag == "title":
                        if " TS " in child.text:
                            bad = True
                            break
                        tmpRelease["title"] = child.text
                    elif child.tag == "pubDate":
                        tmpRelease["releaseDate"] = datetime.datetime.strptime(child.text, "%a, %d %b %Y %H:%M:%S +0000")
                    
                i = i + 1
                if not bad:
                    releases.append(tmpRelease)
                    
            if releases != []:
                return releases
            
        return []
    
    def queryTorrentz(self, movie, typ):
        
        ###typ = (0,1) - (SQ, HD)
        
        data = {"title": movie.title, "year": movie.year, "typ": typ}
        data = self._queryTorrentzHelper(data)       
        
        if data == []:
            print("torrentz data empty")
            return
        for d in data:            
            rls = getReleaser(movie.title, d["title"])
            if not rls or movie.hasRelease(rls):
                continue
            else:
                r = Release(typ, self._fetchMagnetFromHash(d["hash"]), d["releaseDate"])
                #r = Release(typ, None, d["releaseDate"])
                tmpData = {}
                tmpData["size"] = d["size"]
                tmpData["seeds"] = d["seeds"]
                tmpData["peers"] = d["peers"]
                tmpData["hash"] = d["hash"]
                tmpData["rls"] = rls
                r.data = tmpData
            movie.releases.append(r)
    
    def updateTorrentz(self, movie):
        for i in range(len(movie.releases)):
            R = movie.releases[i]
            seeds, peers = self._fetchTorrentzInfoUpdate(R.data["hash"])
            if seeds + peers == -2:
                R = None
            R.data["peers"] = peers
            R.data["seeds"] = seeds
            
        movie.releases[:] = [R for R in movie.releases if R is not None]
    
    def _fetchTorrentzInfoUpdate(self, hsh):
        url = "http://torrentz.eu/" + hsh
        html = self.scrape(url)
        soup = bs4.BeautifulSoup(html)
        seeds, peers = -1, -1
        
        for div in soup.body.find_all("div"):
            if div.has_key("class"):            
                if div["class"][0] == "trackers":
                    for span in div.dl.dd.find_all("span"):
                        if span.has_key("class"):
                            if span["class"][0] == "u":
                                seeds = int(span.string)
                            elif span["class"][0] == "d":
                                peers = int(span.string)
        return seeds, peers

    def _fetchMagnetFromHash(self, hsh):
        url = "http://torrentz.eu/" + hsh
      
        fp = open(TORRENT_WEBSITES, "r")
        sortedSites = json.load(fp)
        fp.close()

        gathered = {}
        
        ### Gather all the sites with magnet, that poses this torrent
        
        html = self.scrape(url)
        if not html:
            return
        
        soup = bs4.BeautifulSoup(html)
        for div in soup.body.find_all("div"):
            try:
                if div["class"][0] == "download":
                    for dl in div:
                        try:
                            gathered[dl.dt.a.span.string] = dl.dt.a["href"]          
                        except:
                            pass
            except:
                pass
 
        for site, link in gathered.items():
            for sites in sortedSites:
                if site in sites:
                    link = self._fetchMagnet(link)
                    if link:
                        return link
    
    def _fetchMagnet(self, url):
        try:
            html = self.scrape(url)                
            frOm = html.find("\"magnet:?")
            if frOm < 0:
                return None
            tO = html.find("\"", frOm+1)
            html = html[frOm+1:tO]
            
            tO = html.find("&amp;")
            tO_2 = html.find("&dn=")
            tO = (tO != -1) * tO + (tO == -1) * tO_2
            
            if tO != -1:
                html = html[0:tO] 
            return html
        except:
            pass
        
    def instaWatcherUpdate(self, lastCheck = 0, new = True, all = False):
        
        '''
        if not 4 < now.hour - 6 < 8:
            return None
        '''
        
        url = "http://instantwatcher.com/titles/"
        if new:
            url += "new"
        else:
            url += "expiring"
        url += "?tv_filter=movies+only&min_rating=3.0&earliest_year=1950&?view=minimal"
        html = self.scrape(url)
        soup = bs4.BeautifulSoup(html)
        
        for ul in soup.body.div.find_all("ul"):
            if ul.has_key("id"):
                if ul["id"] == "title-listing":
                    titles = ul
        
        releases = {}
        i = 0
        for li in titles.find_all("li"):
             
            if li.div["class"][0] == "title-group":

                _date = datetime.datetime.strptime(li.div.text, "%b %d").date()
                _date = _date.replace(datetime.date.today().year)
                
                # if new, date is before today, or else switch to previous year
                if new and _date > datetime.date.today():
                    _date = _date.replace(_date.year - 1)
                #if expiring, date if after today, or else switch to next year
                if not new and datetime.date.today() > _date:
                    _date = _date.replace(_date.year + 1)
                #last lines are probably buggy :)
            
            
            try:
                title = li.a.text
                year = li.span.text
                data = self._queryOmdbApiHelper(title = title, year = year)
                id_IMDB = int(data["imdbID"][2:])
            except:
                continue
            
            r = Release(3, releaseDate = _date)
            
            txt = str(li)
            index1 = txt.find("WiPlayer?movieid=") + 17
            index2 = txt[index1:].find("\'")
            
            r.link = int(txt[index1:index1 + index2])  
            
            HD = False
            if txt.find("class=\"hd\"") != -1:
                HD = True
            
            r.data["HD"] = HD
            
            releases[id_IMDB] = r
            i += 1
            if i == 5:
                break
        
        return releases
        
    def queryAmazon(self, movie):
        return 0
   

if __name__ == "__main__":
    

    f = Fetcher()
    ms = f.instaWatcherUpdate(new = False)
    for k,v in ms.items():
        m = Movie(id_IMDB = k)
        f.queryOmdbApiFull(m)
        f.queryRottenTomatoMovie(m)
        f.queryTorrentz(m, 0)
        print(m)
        for r in m.releases:
            print(r)
        
        input("stisn")
    
    
    '''
    f = Fetcher()
    f._fetchMagnetFromHash("188aa63c64e1d6b64b74f5be36cb9244c08a3456")
    m = Movie()
    m.title = "The Godfather"
    m.year = 1974
    ret = f.queryTorrentz(m, 0) 
    
    for r in m.releases:
        print(r)
    '''
    
    
    
    '''
    ret = f._queryTorrentzHelper({"title": "wreck it ralph"})
    for r in ret:
        tajm = r["releaseDate"]
    

    hshs = ["188aa63c64e1d6b64b74f5be36cb9244c08a3456", 
            "188aa63c64e1d6b64b74f5be36cb9244c08a3456", 
            "83093cf4fb27e4874d14f60d483aef3c7959e0a0", 
            "24a090e2e44aeaca73c81aabc97eaf9c7c20af24", 
            "e4419bbaafb2326b613d145aaa2342957c578d8c", 
            "6d7882c59d6555283745f31e0492ac8d041132a1", 
            "a8e59139ddd8ab84c4d46104f0a6a7432c6530ca", 
            "e39b837c003fa6e23aaf18fe4a02541ce19445c9", 
            "0e7cb7bf1f3b855a1f653c98a8ab1e95f9aa089a",
            "fd3bc2ee4e11773186db9758b14b1c17f1acbed5",
            "c0b85bde9dde3b56c78ff29f00bae24b1493abce",
            "ce1fc50bffb09962be8f3c49478cbeb65e2afe0f",
            "a0c2982e0b45552cd46284db6563a1a2112bce67",
            "3c64a0ddf992e106abf2af938bceb76488d2583e",
            "9208cc67483704c84096d9747b4ed970e56bc8ac",
            "d9f7719922d00d4f2ae59c514dc2aee7a2938dc9",
            "90851fdb47636d9274eb546407be5f484a3a49a6",
            "b2bc9f66a6ac77d5e80db4d4f6a7bd8242c98dca",
            "a29743e386acc7814d5b96b8246125f9a24f4151",
            "1c1cd66edc73cf14e5db5bd54b244aab737087a9",
            "e2f5358dad9ad33cbdf7248abab957e9996eef4f",
            "7875fa4e577d30f0caab833616c3f6a6d02bc173",
            "1722a4c54d8d4ee60ca89e2d49f04a152d4b72d7",
            "609de93708cd15deaa6e1adac399590691cc4cfd",
            "80898ab7f1597e65d69ede2c7e40e0ac369f65c6",
            "9208cc67483704c84096d9747b4ed970e56bc8ac",
            "245f9f9e5458748e7582a09883e7879c050be3d6",
            "c80497de8157dc3417bc386a633361c2573e2552",
            "92b846558fdd4fbaacfb2cfc3772cab545b4e943",
            "2c8d4e9a70037ea02f2248810ea678381c19eb6f",
            "b0873a3dea67c02dcef1bfa360eb7ab09a40aec6",
            "b0a0c269c36a874d717f79670803020c29258f80",
            "a4850d6810353bb5abcee94696ce8ef56e9a5198",
            "97fcb67b12232635260662783981b71183cd1af8",
            "6ab51c7844ff6c57bd5881c58f13b5ad5d05e766",
            "ecf1de43a7fd1dda110c99a2cf83dd1532e811fd",
            "a91b28be435abf3e33f0c732c82a490e9ae607c4",
            "426999574f12d1a737d5e54f041985e37230f510"]
    
    for h in hshs:
        a = f._fetchMagnetFromTorrentzHelper(h)
        print(a)

        '''