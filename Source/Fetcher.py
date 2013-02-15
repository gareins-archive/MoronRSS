'''
Created on Feb 13, 2013

@author: ozbolt
'''

APIKEY_RT = "zj3y2qsm6q2t5pef2spv7bnd"

import urllib.request, urllib.error
import json
from Base import Movie
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
        - "typ" (let's say dvdrip)
        - "rls" (lets say maxspeed)
        '''
        
        url = "http://torrentz.eu/feed?q="
        if "title" in data:
            url = url + data["title"].replace(" ", "+") + "+"
        if "year" in data:
            url = url + str(data["year"]) + "+"
        if "typ" in data:
            url = url + data["rlsType"] + "+"
        if "rls" in data:
            url = url + data["rls"]
        
        xml = self.scrape(url)
        root = etree.fromstring(xml)[0]
        
        releases = []
        i = 0
        
        while len(releases) < noOfResoults and i < len(root):
            if root[i].tag != "item":
                i = i + 1
                continue
            
            tmpRelease = {}
            small = False
            
            for child in root[i]:
                if child.tag == "description":
                    tmpData = {}
                    description = re.split('[a-z]+: ', child.text, flags=re.IGNORECASE)
                    tmpData["seeds"] = int(description[2].replace(",", ""))
                    
                    if "KB" in description[1] or len(description[1]) < 6 or tmpData["seeds"] < minSeeds:
                        small = True
                    else:
                        tmpData["size"] = int(description[1][0:-3])
                        tmpData["peers"] = int(description[3].replace(",", ""))
                        tmpData["hash"] = description[4]
                    tmpRelease["data"] = tmpData
                elif child.tag == "title":
                    tmpRelease["title"] = child.text
                #elif child.tag == "pubDate":
                    #tmpRelease["releaseDate"] = datetime.datetime.strptime(child.text, "%a, %d %b %Y %H:%M:%S +0000")
                
            i = i + 1
            if small:
                continue                    
            releases.append(tmpRelease)
        '''
        for r in releases:
            for k,v in r.items():
                print(k,":",v)
            print("\n")
        '''
            
        return releases
        
        #print(etree.tostring(root).decode("utf8"))
 
   
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
    print(1)
        
        
        
        
        
        
        
        
        
        