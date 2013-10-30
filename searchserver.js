var http = require('http')
  , url = require('url')
  , google = require('google-tools')
  , mu   = require('mu2');

mu.root = __dirname + '/templates';

console.log("pre create")

http.createServer(function (req, web_out) {

    var kw = url.parse(req.url, true).query['q'];

    if (process.env.NODE_ENV == 'DEVELOPMENT') {
        mu.clearCache();
    }

    google.search({q: kw}, function(err, resultados){
        //console.log(kw);
        var stream = mu.compileAndRender('index.html', {varios: resultados['results']});
        stream.pipe(web_out);
    });
}).listen(8000, '127.0.0.1');

console.log("post create")
