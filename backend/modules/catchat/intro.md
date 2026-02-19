这是一个大概的计划

catchat是我们的聊天平台。这里只做后端。
目前，只能发消息，不做发图片等。
消息用postgres数据库保存。
如果是admin身份（main users表格中，admin身份），可以选择给所有用户发消息，否则就只能一次一个。
我们现在有一个用username对应用户id的api端口，用这个，可以搜索到这个用户名，然后点进去就可以发消息。

本平台使用railway部署，postgres数据库建表非常简单：请把建表脚本写进main,py，用强注释comment说明，等到推送到github，railway会自动部署，等部署好了，就可以把临时代码删除，表格自动建立。
如下是环境变量：
CATCHAT_DATABASE=postgresql://postgres:aSSULNTjkonVmzZRZAuulIfVvlILcXsh@postgres-dca5ee5d.railway.internal:5432/railway
CATCHAT_PUBLIC_DATABASE=postgresql://postgres:aSSULNTjkonVmzZRZAuulIfVvlILcXsh@switchyard.proxy.rlwy.net:52364/railway