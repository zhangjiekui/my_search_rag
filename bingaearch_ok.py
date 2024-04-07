import requests
from bs4 import BeautifulSoup
class bing:
    def __init__(self):
        '''
        bing请求类
        
        Dict:
        header
        
        Function:
        __init__(self)
        make_url(self,q,data='chinese',pagenum='1')
        jx(self,url)

        Returns
        -------
        None.

        '''
        self.header = {
            'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36 Edg/108.0.1462.76'
            }


    def make_url(self,q,data='chinese',pagenum='1'):
        '''
        生成必应url
        
        Parameters
        ----------
        q : str
            关键字
            data : str, optional
            'chinese' or 'english'. The default is 'chinese'.
            pagenum : str, optional
            The default is '1'.
            
            Returns
            -------
            url.

        '''
        if data != 'chinese' and data != 'english':
            assert data != 'chinese' and data != 'english', '不支持中英文以外的文字'
    
        if data == 'chinese':
            urls = 'https://cn.bing.com/search?q='+q+'&form=ANSPH1'
        elif data == 'english':
            urls = 'https://cn.bing.com/search?q='+q+'&FORM=BESBTB&ensearch=1'
                
        if pagenum == '1':
            return urls
        r = requests.get(urls,headers = self.header)
        s = BeautifulSoup(r.text,'html5lib')
        # s = BeautifulSoup(r.text,'html.parser')
        page = s.find('li',class_ = 'b_pag')
        pages = page.find_all('li')
        pageurls = {}
        for i in pages:
            try:
                pageurls[i.text] = i.find('a')['href']
            except:
                pass
    
        try:
            return pageurls[pagenum]
        except:
            return urls
    
    

    def jx(self,url):
        '''
        请求并解析url

        Parameters
        ----------
        url : str
            usually from function make_url.

        Returns
        -------
        None.

        '''
        r = requests.get(url,headers = self.header)
        # s = BeautifulSoup(r.text,'html.parser')
        s = BeautifulSoup(r.text,'html5lib')
        lis = s.find_all('li',class_ = 'b_algo')

        urls = []

        for i in lis:
            url=i.find('a',class_ = 'tilk')['href']
            urls.append(url)
        return urls
    
if __name__ == '__main__':         
    k = bing()

    qs = ['langchain最新版本','安徽晶奇网络科技股份有限公司','中国科学技术大学','张结魁']
    for q in qs:
        print('=========================')
        url = k.make_url(q)         
        rlist = k.jx(url)
        print(f'[{q}]:{url}')
        print(f'共搜索到{len(rlist)}条记录')
        for i,_url in enumerate(rlist):
            print(f'[{i}]:{_url}')
