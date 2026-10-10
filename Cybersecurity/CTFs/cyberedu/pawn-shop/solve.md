┌──
└─$ curl -i -H "Origin: https://bit-sentinel.com" http://34.40.88.204:31966/product/flag
HTTP/1.1 200 OK
Server: Werkzeug/3.0.1 Python/3.12.3
Date: Sat, 10 Oct 2026 16:09:50 GMT
Content-Type: text/html; charset=utf-8
Content-Length: 792
Access-Control-Allow-Origin: https://bit-sentinel.com
Vary: Origin
Connection: close

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Flag</title>
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>

    <!--There is no "Add to Cart" option. This is not even a working shop.-->

    <header>
        <h1>Flag</h1>
    </header>

    <main class="product-page">
        <img src="/static/images/flag.jpg">
        <h2>Flag</h2>
        <p>It&#39;s ok I guess.</p>
        <span class="price">$13.37</span>
        <br>

        <p>CTF{545d97580ec061a2f8076d2ec972906bf3c3fde454d38965ea4e18f61d474a7f}
</p>
        <br>

        <a href="/">
            <button class="back-btn">Back to Store</button>
        </a>
    </main>

</body>
</html>
┌──
└─$

flag:
**CTF{545d97580ec061a2f8076d2ec972906bf3c3fde454d38965ea4e18f61d474a7f}**