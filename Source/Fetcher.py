'''
Created on Feb 13, 2013

@author: ozbolt
'''

APIKEY_RT = "zj3y2qsm6q2t5pef2spv7bnd"

import urllib.request, urllib.error
import json
from Base import Movie, Release
import datetime
import bs4
from lxml import etree
import re
from Tools import *


class Fetcher(object):
    '''
    classdocs
    '''
            
    def scrape(self, someurl):
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
            return html

        except urllib.error.HTTPError as e:
            print(e.code)
            print(e.read())
        except UnicodeDecodeError as e:
            return "<html></html>"
            pass
            
    def queryOmdbApiHelper(self, data):
        url = "http://www.omdbapi.com/?"
        
        for k,v in data.items():
            url += k + "=" +  (str)(v).replace(" ", "+") + "&"
        url+="plot=full"
        
        data = self.scrape(url)    
        return json.loads(data)
    
    def queryOmdbApi(self, data):
        
        data = self.queryOmdbApiHelper(data)
        toRet = Movie()
        
        try:
            toRet.plot = data["Plot"]
            toRet.title = data["Title"]
            
            if data("Poster") != "N/A":
                toRet.linkPhoto = data["Poster"]
            else:
                toRet.linkPhoto = ""
                
            toRet.director = data["Director"]
            toRet.dateRelease = datetime.datetime.strptime(data["Released"], "%d %b %Y" )
            toRet.actor = data["Actors"].split(", ")
            toRet.genre = data["Genre"].split(", ")
            toRet.IMDB_rating = float(data["imdbRating"])
            toRet.IMDB_votes = int(data["imdbVotes"].replace(",", ""))
            toRet.id_IMDB = int(data["imdbID"][2:])
            runtime = data["Runtime"].split(" ")
            if "h" in runtime:
                h = int(runtime[0])
                m = int(runtime[2])
            else:
                h = 0
                m = int(runtime[0])
            toRet.runTime = h*60 + m   
        except:
            print("fuck")

        return toRet
    
    def queryOmdbApiQuickUpdate(self, movie):
        '''
        Updating:
        - imdbRating
        - imdbVotes
        '''        
        
        data = {}
        data["i"] = "tt0000000"[:9 - len('%d' % movie.id_IMDB)] + str(movie.id_IMDB)
        newData = self.queryOmdbApiHelper(data)
        
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
            raise
        
    def queryRottenTomatoUpcomming(self):
        url = "http://api.rottentomatoes.com/api/public/v1.0/lists/movies/upcoming.json?page_limit=10&page=1&country=us&apikey=" + APIKEY_RT
        response = self.scrape(url)
        
        data = json.loads(response)
        #print(json.dumps(data, sort_keys=True, indent=4, separators=(',', ': ')))
        
        movies = []
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
            m.dateRelease = datetime.datetime.strptime(movie["release_dates"]["theater"], "%Y-%m-%d")
            m.linkPhoto = movie["posters"]["original"]
            m.runTime = movie["runtime"]
            m.id_RT = movie["id"]
                        
            movies.append(m)

        #for m in movies:
            #print(m)
            
        return movies
    
    def queryYoutubeTrailerHelper(self, title, year, maxResoults = 5, official = True, HD = True):
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
            dur = int(group.find("{http://search.yahoo.com/mrss/}content").get("duration"))
            if 60 > dur or dur > 500:
                continue
            tmpMovie["id"] = group.find("{http://gdata.youtube.com/schemas/2007}videoid").text
            ytmovies.append(tmpMovie)
        
        if ytmovies == []:
            return "RT"
        
        mov = 0
        for i in range(len(ytmovies)):
            if i==0:
                continue
            if ytmovies[i]["cmp"] > ytmovies[mov]["cmp"] + 0.05:
                mov = i
        
        return ytmovies[mov]["id"]
    
    def queryYoutubeTrailer(self, movie):
        trailer = self.queryYoutubeTrailerHelper(movie.title, movie.year)
        if trailer == "RT":
            trailer = self.queryYoutubeTrailerHelper(movie.title, movie.year, HD = False)
        if trailer == "RT":
            trailer = self.queryYoutubeTrailerHelper(movie.title, movie.year, official = False, HD = False)
        return trailer
  
    def queryTorrentzHelper(self, data, minSeeds = 10, noOfResoults = 5):
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
            url = url + "dvdrip" + "+"
        elif data["typ"] == 1:
            mIn, mAx = 2000, 10000
            url = url + "1080p" + "+"
        else:
            raise
        
        xml = self.scrape(url)
        root = etree.fromstring(xml)[0]
        
        releases = []
        i = 0
        
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
            if bad:
                continue                    
            releases.append(tmpRelease)
            
        return releases
    
    def queryTorrentz(self, movie, typ):
        
        ###typ = (0,1) - (SQ, HD)
        
        data = {"title": movie.title, "year": movie.year, "typ": typ}
        data = self.queryTorrentzHelper(data)       
        
        if data == []:
            return
        for d in data:
            rls = getReleaser(movie.title, movie.year, d["title"])
            if movie.hasRelease(rls):
                continue
            else:
                r = Release(typ, self.fetchMagnetFromHash(d["hash"]), d["releaseDate"])
                tmpData = {}
                tmpData["size"] = d["size"]
                tmpData["seeds"] = d["seeds"]
                tmpData["peers"] = d["peers"]
                tmpData["hash"] = d["hash"]
                tmpData["rls"] = rls
                r.data = tmpData
            movie.releases.append(r)
    
    def updateMovieReleases(self, movie):
        for R in movie.releases:
            #if R.type == 3:
                #netflix, program in later
            #elif R.type == 4
                #ama\on, later
            #else:
            seeds, peers = self.fetchTorrentzInfoUpdate(R.data["hash"])
            if seeds + peers == -2:
                raise
            R.data["peers"] = peers
            R.data["seeds"] = seeds
    
    def fetchTorrentzInfoUpdate(self, hsh):
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

    def fetchMagnetFromHash(self, hsh):
        url = "http://torrentz.eu/" + hsh
        sortedSites = [
                     [
                      "bitsnoop.com",
                      "rarbg.com"
                      ],
                     [
                      "torrents.net",
                      "thepiratebay.se",
                      "torrentreactor.net",
                      "1337x.org",
                      "monova.org",
                      "torrentcrazy.com",
                      "movietorrents.eu",
                      ],
                     [
                      "torrentdownloads.me", 
                      "kickasstorrents.com", 
                      "seedpeer.me",
                      "extratorrent.com", 
                      "thepiratebay.org",
                      ],
                     [
                      "h33t.com", 
                      "fenopy.se",
                      "vertor.com",
                      "torrentzap.com",
                      "kat.ph"
                      ]
                     ]

        gathered = {}
        
        ### Gather all the sites with magnet, that poses this torrent
        
        html = self.scrape(url)
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
                    link = self.fetchMagnet(link)
                    if link:
                        return link
    
    def fetchMagnet(self, url):
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
 
   
def getTrackerList():
    '''
    fetcher = Fetcher()
    searchAll = ["3d","2012","ita","2013","american beauty","arab","arrow","axxo","bluray","comics","criminal","minds","csi","dvdrip","ebook","french","games","hindi","movie","king kong","2011","journey","goblet of fire","justified kingdom","release","malayalam","movies","maxspeed","modern","pc games","red dawn","side effects","skyfall","software","southland","superman","swesub","tamil","dark knight","iron man","ice age","shrek","finding nemo","wii","window 7","workaholics",]
    allDownloaded = []
    for s in searchAll:
        data = {"title": s}
        tmp = fetcher.queryTorrentzHelper(data, minSeeds = 50, noOfResoults = 30)
        allDownloaded.append(tmp)
    
    f = open("allData.json", "w")
    json.dump(allDownloaded, f)
    f.close()
    
    '''
    '''
    sys.stdout = Logger("yourlogfilename.txt")  
    
    f = open("allData.json", "r")  
    data = json.load(f)
    
    dontUse = ["avi", "wtf", "p2p", "audio", "movie", "ita", "eng", "subs", "nem", "hdtv", "subs", "x264"] 
    
    for d1 in data:
        for d in d1:
            upload = True
            s = d["title"]
            for dnt in dontUse:
                if dnt in s[-6:].lower():
                    print("\t\t\t\t\tused")
                    upload = False
            if upload:
                lst = s.split(" ")
                if len(lst[-1]) < 3:
                    upload = False
                    print("\t\t\t\t\tshort")
            if upload:
                print(s[-20:])
        
    f.close()
    '''
    return 0



if __name__ == "__main__":
    m = Movie()
    m.title = "finding nemo"
    m.year = 2003
    
    f = Fetcher()
        
    f.queryTorrentz(m, 0)
    print(m.releases)

    
    '''
    ret = f.queryTorrentzHelper({"title": "wreck it ralph"})
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
        a = f.fetchMagnetFromTorrentzHelper(h)
        print(a)
    
        
        
        
        
        
        
        
        
        
        '''