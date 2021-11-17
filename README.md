# Web Crawler
* Booking.com_Hotel：爬取 Booking.com 飯店。
* Booking.com_Review：爬取 Booking.com 住客評語。 
* PTT_Board：爬取 PTT 文章。
## 安裝套件
* Booking.com_Hotel：
```
pip install bs4
pip install fake_useragent
pip install numpy
pip install pandas
pip install requests
pip install lxml
```
* Booking.com_Review：
```
pip install bs4
pip install fake_useragent
pip install numpy
pip install requests
pip install urllib3
pip install lxml
```
* PTT_Board：
```
pip install bs4
pip install pandas
pip install requests
pip install lxml
```
## 執行方法
* Booking.com_Hotel：
```
$ python BookingHotel.py
```
* Booking.com_Review：
```
$ python BookingReview.py
```
* PTT_Board：
```
$ python PTTBoard.py [看板名稱] [起始頁面(倒數)] [抓取頁數] [檔名]
```
