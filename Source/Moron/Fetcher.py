'''
Created on Feb 13, 2013

@author: ozbolt
'''

import urllib.request, urllib.parse, urllib.error
import json
from Base import Movie
import datetime

class Fetcher(object):
    '''
    classdocs
    '''

    def __init__(self):
        '''
        Constructor
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
            movie.IMDB_rating = float(newData["imdbRating"])
            movie.IMDB_votes = int(newData["imdbVotes"].replace(",", ""))
        except:
            print("Update data not avaliable")
            raise
 

if __name__ == "__main__":
    fetcher = Fetcher()
    
    movie = Movie(title = "Life is beautiful", id_IMDB = 1114690, IMDB_votes = 10)
    print(movie.IMDB_votes)
    fetcher.queryOmdbApiQuickUpdate(movie)
    print(movie.IMDB_votes)
    
    
    
    
    
    
    
    
        