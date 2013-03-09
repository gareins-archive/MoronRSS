#!/usr/bin/python3

'''
To Do:
- Amazon prime update and search
- LoveFilm update and search
- Wrapper for new movies to automatically check LoveFilm, Netflix and Amazon
- checkReleases wrapper for all releases
- Pack all URLs in a constant?
- add instawatcher blocker
- bs4 attr!! clean previous!
- add real Update to RTs
- check if release allready in

@author: ozbolt
'''

from Base import Movie, Release
from Tools import *
from MoronicExceptions import *
from Keys import APIKEY_RT

from urllib.parse import urlparse
from datetime import datetime, date, timedelta
import sys
import threading

import bs4
from lxml import etree
import requests


class Fetcher(threading.Thread):
    
    q = ""
    m = None 
    
    def run(self):
                
        if self.q == "movieDetails":
            self.queryMovieDetails(self.m)
        elif self.q == "movieUpdate":
            self.queryOmdbApiUpdate(self.m)
            self.queryRottenTomatoMovie(self.m)
        elif self.q == "upcoming":
            return self.queryRottenTomatoList("U")
        elif self.q == "boxOffice":
            return self.queryRottenTomatoList("B")
        elif self.q == "dvdReleases":
            return self.queryRottenTomatoList("D")
        elif self.q == "trailer":
            self.queryYoutubeTrailer(self.m)
        elif self.q == "netflix":
            return self.queryInstaWatcher(self.m)
            
    def scrape(self, url, params = {}):
        
        i = 0
        while True:
            netloc = urlparse(url).netloc
            
            lock = checkLock_andLock(netloc)                
            if not lock:
                break
            elif i < 10:
                sleep(1)
                i = i + 1
            elif i == 10:
                #force unlocking resource??
                #10 seconds enough
                lockUrl(netloc)
                break
            else:
                raise ResourceBusy(netloc)
        
        try:
            r = requests.get(url, params=params)
            html = r.text
            print("scraped:", r.url)
            sys.stdout.flush()
            
            f = open(URLS_LOCK, "r")
            locks = json.load(f)
            f = open(URLS_LOCK, "w")
            locks[netloc] = False
            json.dump(locks, f)
            f.close()
            
            return html
            
        except requests.exceptions.ConnectionError:
            raise ResourceUnavaliable(netloc)
        
    def fetchMovieUpdate(self, movie):
        self.fetchOmdbApiUpdate(movie)
        self.fetchRottenTomatoUpdate(movie)    
        
    def _queryOmdbApiHelper(self, title = "", id_IMDB = -1, year = -1):
        url = "http://www.omdbapi.com"
        params = {"plot": "full"}
        
        i = ""
        if id_IMDB != -1:
            i = "tt0000000"[:9 - len('%d' % id_IMDB)] + str(id_IMDB)
            params["i"] = i
        else:
            params["y"] = year
            params["t"] = title
        
        jsonData = self.scrape(url, params)
        data = json.loads(jsonData)        
                
        if data["Response"] == "False":
            raise ResourceEmpty("www.omdbapi.com")
        return data
     
    def _omdbApiHelper(self, movie, update = False):
        
        if movie.id_IMDB != -1:
            data = self._queryOmdbApiHelper(id_IMDB = movie.id_IMDB)
        else:
            data = self._queryOmdbApiHelper(title = movie.title, year = movie.year)
        
        movieDict = movie.constructDict()        
        
        #if (data contains what i want) and (if i am updating, some data if already in should not be changed)
        
        if ("Title" in data) and not (update and ("title" in movieDict)):
            movie.title = data["Title"]
        if "Year" in data and not (update and ("year" in movieDict)) :
            movie.year = data["Year"]
        if "imdbID" in data and not (update and ("title" in movieDict)):
            movie.id_IMDB = int(data["imdbID"][2:])
        if data["Runtime"] != "N/A" and not (update and ("runTime" in movieDict)):
            runtime = data["Runtime"].split(" ")
            if "h" in runtime:
                h = int(runtime[0])
                m = 0
                if "m" in runtime or "min" in runtime:
                    m = int(runtime[2])
            else:
                h = 0
                m = int(runtime[0])
            movie.runTime = h*60 + m
        
        if data["imdbRating"] != "N/A":
            movie.IMDB_rating = float(data["imdbRating"])
        if data["imdbVotes"] != "N/A":
            movie.IMDB_votes = int(data["imdbVotes"].replace(",", ""))
        if "Director" in data:
            movie.director = data["Director"]
        if "Actors" in data:
            movie.actors = data["Actors"].split(", ")
        if "Genre" in data:
            movie.genres = data["Genre"].split(", ")
        if "Plot" in data:
            movie.plot = data["Plot"]
        if  data["Released"] != "N/A":
            dajt = datetime.strptime(data["Released"], "%d %b %Y" )
            movie.dateRelease = date(dajt.year, dajt.month, dajt.day)
        if movie.linkPhoto == "" and data["Poster"] != "N/A":
            movie.linkPhoto = data["Poster"]
        
    def fetchOmdbApiUpdate(self, movie):
        self._omdbApiHelper(movie, update = True)
    
    def queryOmdbApiFull(self, movie):
        self._omdbApiHelper(movie)
    
    def fetchOmdbApiFull(self, movie):
        self._omdbApiHelper(movie)
        
    def _rottenTomatoeHelper(self, scraped, movie, update = False):
        ### This is data, that is always overwrites data from other sources 
        movie.id_RT = int(scraped["id"])         
        if "critics_score" in scraped["ratings"]:
            movie.rt_critics = scraped["ratings"]["critics_score"]
        if "audience_score" in scraped["ratings"]:
            movie.rt_audience = scraped["ratings"]["audience_score"]
        if "synopsis" in scraped:
            if len(scraped["synopsis"]) > 20:
                movie.plot = scraped["synopsis"]
        if "posters" in scraped:
            if "original" in scraped["posters"]:
                movie.linkPhoto = scraped["posters"]["original"]
        if "abridged_cast" in scraped:
            movie.actors = scraped["abridged_cast"]
            for a in movie.actors:
                a.pop("characters", 0)
        ###only in full update...
        if "abridged_directors" in scraped:
            movie.directors = []
            for director in scraped["abridged_directors"]:
                movie.directors.append(director["name"])
        if "genres" in scraped:
            movie.genres = scraped["genres"]

        ### This checks for already avaliable data and does not overwrite           
        if movie.dateRelease == None and "theater" in ["release_dates"]:
            movie.dateRelease = datetime.strptime(["release_dates"]["theater"], "%Y-%m-%d")
        if movie.runTime == -1 and "runtime" in scraped:
            movie.runTime = scraped["runtime"]
    
    def queryRottenTomatoList(self, listType, resoultLen = 20):
        
        url = "http://api.rottentomatoes.com/api/public/v1.0/lists"
        if listType == "U":
            url += "/movies/upcoming.json?"
        elif listType == "B":
            url += "/movies/box_office.json?"
        elif listType == "D":
            url += "/dvds/new_releases.json?"
        
        params = {"page": 1,
                  "page_limit": resoultLen,
                  "country": "us",
                  "apikey": APIKEY_RT}
        
        response = self.scrape(url, params)
        
        data = json.loads(response)
        
        movies = []
        i = 1
        for res in data["movies"]:
            try:
                res["alternate_ids"]["imdb"]
            except:
                continue
            m = Movie()
            m.id_IMDB = int(res["alternate_ids"]["imdb"])
            m.title = res["title"]
            m.year = res["year"]
            m.id_RT = int(res["id"])
            self._rottenTomatoeHelper(res, m)
            
            if listType == "D":
                m.boxOffice = i
                i = i+1
                        
            movies.append(m)
            
        return movies
    
    def queryRottenTomatoMovie(self, movie):
        url = "http://api.rottentomatoes.com/api/public/v1.0/movies.json?"
        params = {"q": movie.title + " %s" % movie.year,
                  "page_limit": 3,
                  "apikey": APIKEY_RT}
        
        returned = self.scrape(url, params)        
        returned = json.loads(returned)
        
        #print(json.dumps(returned, indent = "  "))
        
        if returned["total"] == 0:
            return
        
        for res in returned["movies"]:
            
            if int(movie.year) != res["year"]:
                continue #for performance reason double if
            elif strCmp(movie.title, res["title"]) < 0.95 and (movie.title.lower() not in res["title"].lower()):
                continue
            self._rottenTomatoeHelper(res, movie)
            
            return 

    def fetchRottenTomatoUpdate(self, movie):
        
        url = "http://api.rottentomatoes.com/api/public/v1.0/movies/%d.json" % movie.id_RT
        params = {"apikey": "zj3y2qsm6q2t5pef2spv7bnd"}
        resp = self.scrape(url, params)
        data = json.loads(resp)
        
        movie.rt_critics = data["ratings"]["critics_score"]
        movie.rt_audience = data["ratings"]["audience_score"]
     
    def fetchRottenTomatoTrailer(self, movie):
        url = "http://api.rottentomatoes.com/api/public/v1.0/movies/%d/clips.json?" % movie.id_RT 
        params = {"apikey": "zj3y2qsm6q2t5pef2spv7bnd"}
        resp = self.scrape(url, params)
        data = json.loads(resp)
        
        if data["clips"]:
            movie.addTrailer({"type": "RT", "link": data["clips"][0]["links"]["alternate"][32:], "score": 0.8})
        
    def _queryYoutubeTrailerHelper(self, title, year, maxResoults = 3, official = True, HD = True):
        deficit = 0
        if official: 
            query = title + " official trailer" 
            deficit += 2
        else:
            query = title + " trailer"
        
        if HD:
            deficit += 2
            HD = "true"
        else:
            HD = ""
        
        url = "http://gdata.youtube.com/feeds/api/videos"
        params = {"v": 2, 
                  "q": query,
                  "max-results": maxResoults,
                  "hd": HD}
        
        xml = self.scrape(url, params)
        xml = xml[xml.find(">")+1:] #removing first not well-formatted tag, leaving well formatted xml
        
        root = etree.fromstring(xml)        
        entries = root.findall("{http://www.w3.org/2005/Atom}entry")

        trailers = []
        resultNum = 0
        for entrie in entries:
            tmpTrailer = {"type": "YT"}
            tmpT = entrie.find("{http://www.w3.org/2005/Atom}title").text
            tmpTrailer["score"] = round(trailerCheck(query, tmpT, year) * 10/(10+resultNum+deficit), 3)
            resultNum += 1
            if tmpTrailer["score"] < 0.4:
                continue
            group = entrie.find("{http://search.yahoo.com/mrss/}group")
            try:
                dur = int(group.find("{http://search.yahoo.com/mrss/}content").get("duration"))
                if 60 > dur or dur > 500:
                    continue
            except:
                pass
            tmpTrailer["link"] = group.find("{http://gdata.youtube.com/schemas/2007}videoid").text
            trailers.append(tmpTrailer)
        
        return trailers
    
    def queryYoutubeTrailer(self, movie):
        trailers = self._queryYoutubeTrailerHelper(movie.title, movie.year)
        if not trailers:
            trailers = self._queryYoutubeTrailerHelper(movie.title, movie.year, HD = False)
        if not trailers:
            trailers = self._queryYoutubeTrailerHelper(movie.title, movie.year, official = False, HD = False)
        movie.addTrailers(trailers)
  
    def fetchTorrentReleases(self, movie):
        releases = self.queryTorrentz(movie, 0)
        releases.extend(self.queryTorrentz(movie, 1)) 
        #Release method to add a new release
        #if 2 the same -> typ 0 is deleted        
      
    def _queryTorrentzHelper(self, data, minSeeds = 3, maxReleases = 10):
        '''
        In data:
        - "title"
        - "year"
        - "typ" (0,1)
        !!MAke better syntax of bs4!!!
        '''
        
        url = "http://torrentz.eu/feed"
        movieStr = "%s %s" % (data["title"], data["year"])
            
        if data["typ"] == 0:
            mIn, mAx = 600, 1600
            toTry = ["dvdrip", "webrip"]
        elif data["typ"] == 1:
            mIn, mAx = 1000, 10000
            toTry = ["1080p", "brrip", "bdrip", "720p"]
        else:
            return
        
        releases = []
        
        for rls in toTry:
            params = {"q": "%s %s" % (movieStr, rls)}
            xml = self.scrape(url, params)
            root = etree.fromstring(xml)[0]            
            
            for r in root:
                if len(releases) > maxReleases:
                    break
                if r.tag != "item":
                    continue
                
                tmpRelease = {}
                bad = False
                
                for child in r:
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
                            for f in releases:
                                if tmpRelease["hash"] == f["hash"]:
                                    bad = True
                                    break
                    elif child.tag == "title":
                        if " TS " in child.text:
                            bad = True
                            break
                        tmpRelease["title"] = child.text
                    elif child.tag == "pubDate":
                        tmpDate = datetime.strptime(child.text, "%a, %d %b %Y %H:%M:%S +0000")
                        tmpRelease["releaseDate"] = date(tmpDate.year, tmpDate.month, tmpDate.day)
                
                if not bad:
                    releases.append(tmpRelease)
        
        return releases
    
    def queryTorrentz(self, movie, typ):
        
        ###typ = (0,1) - (SQ, HD)
        
        data = {"title": movie.title, "year": movie.year, "typ": typ}
        data = self._queryTorrentzHelper(data) 
        releases = []      
        
        if data == []:
            return
        for d in data:            
            rls = getReleaser(movie.title, d["title"])
            if not rls or movie.hasRelease(rls):
                continue
            else:
                r = Release(typ, self._fetchMagnetFromHash(d["hash"]), d["releaseDate"])
                tmpData = {}
                tmpData["size"] = d["size"]
                tmpData["seeds"] = d["seeds"]
                tmpData["peers"] = d["peers"]
                tmpData["hash"] = d["hash"]
                tmpData["rls"] = rls
                r.data = tmpData
            releases.append(r)
        
        return releases
    
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
        
    def _fetchInstaWatcherDates(self, release):
        url = "http://instantwatcher.com/titles/%s" % release.data["iw_ID"]
        html = self.scrape(url)
        
        ul = bs4.BeautifulSoup(html).find("ul", {"class": "titleInfo"})
        dates = []
        for li in ul.find_all("li"):
            if "Available" in li.span.text:
                string = li.find("span", {"class": "infodata"}).text
                i = re.search("[A-Z]", string).start(0)
                tmpDate = datetime.strptime(string[i:], "%b %d, %Y ")
                dates.append(date(tmpDate.year, tmpDate.month, tmpDate.day))
        
        release.releaseDate = dates[0] 
        release.data["expiresDate"] = dates[1]    
    
    def _decodeInstaWatcherTitleListing(self, li):
        
        linkEnc = li.find("span", {"class": "play-queue"}).a["onclick"]
        i1 = linkEnc.find(",", 24)
        i2 = linkEnc.find("?movieid=", i1) + 9
        i3 = linkEnc.find("'", i2)
        
        link = int(linkEnc[i2:i3])
        r = Release(3, link, None)
        
        iw_ID = int(linkEnc[24:i1])
        r.data = {"iw_ID": int(iw_ID)}
        
        if li.find("span", {"class": "hd"}):
            r.data["hd"] = True
        else:
            r.data["hd"] = False
        
        self._fetchInstaWatcherDates(r)
        return r
        
    def queryInstaWatcherList(self, days = 3, new = True):#, all = False):
        
        '''
        if not 4 < now.hour - 6 < 8:
            return None
        '''
        
        url = "http://instantwatcher.com/titles/"
        if new:
            url += "new"
        else:
            url += "expiring"
            
        params = {"tv_filter": "movies only",
                  "min_rating": 2,
                  "earliest_year": 1950,
                  "view": "minimal"}
        
        html = self.scrape(url, params)
        soup = bs4.BeautifulSoup(html)
        titles = soup.body.div.find("ul", {"id": "title-listing"})
        
        movies = []
        today = date.today()
        
        for li in titles.find_all("li"): 
            try:
                m = Movie(title = li.a.text, year = li.find("span", {"class": "releaseYear"}).text)
                self.fetchMovieDetails(m)
                if m.id_IMDB < 2:
                    continue
            except ResourceEmpty:
                continue
            
            rls = self._decodeInstaWatcherTitleListing(li)
            if new:
                dateToWatch = rls.releaseDate
            else:
                dateToWatch = rls.data["expiresDate"]
            
            if abs(today-dateToWatch) > timedelta(days = days):
                break
            
            m.releases.append(rls)
            movies.append(m)
        
        return movies
        
    def queryInstaWatcher(self, movie):    
        url = "http://instantwatcher.com/titles"
        params = {"q": "%s %d" % (movie.title, movie.year),
                  "view": "minimal"}
        
        html = self.scrape(url, params)
        #lazy!, slow?:
        ul = bs4.BeautifulSoup(html).find_all("li", {"class": "title-list-item "})
        
        for li in ul:
            title = li.a.text            
            year = int(li.find("span", {"class": "releaseYear"}).text)
            if strCmp(title, movie.title, lower = True) < 0.95 or year != movie.year:
                continue
            linkEnc = li.find("span", {"class": "play-queue"}).a["onclick"]
            i1 = linkEnc.find(",", 24)
            i2 = linkEnc.find("?movieid=", i1) + 9
            i3 = linkEnc.find("'", i2)
            
            link = int(linkEnc[i2:i3])
            r = Release(3, link, None)
            
            iw_ID = int(linkEnc[24:i1])
            r.data = {"iw_ID": int(iw_ID)}
            
            if li.find("span", {"class": "hd"}):
                r.data["hd"] = True
            else:
                r.data["hd"] = False
            
            self._fetchInstaWatcherDates(r)
            movie.releases.append(r)
            return
        
    def queryAmazon(self, movie):
        return 0
   

if __name__ == "__main__":
    
    
    f = Fetcher()
    M = f.queryInstaWatcherList()
    for m in M:
        print(m)
    '''
    for iwli in iwl:
        fetchers.append(Fetcher())
        fetchers[-1].q = "movieDetails"
        m = Movie(id_IMDB = iD)
        M.append(m)
        fetchers[-1].m = m
        fetchers[-1].start()
        
    
    allDead = False
    while not allDead:
        allDead = True
        for f in fetchers:
            if f.isAlive():
                allDead = False            
    
    print("done!")
    

    for m in M:
        print(m)
    '''
    '''
    f = Fetcher()
    m = Movie(title = "Bully", year = 2012)
    f.fetchMovieDetails(m)
    f.fetchRottenTomatoTrailer(m)
    f.queryYoutubeTrailer(m)
    print(m)
    '''