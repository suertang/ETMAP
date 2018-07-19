# coding: utf-8
from bottle import route, run,static_file
from bottle import request
import matplotlib.pyplot as plt
import pandas as pd
from io import BytesIO
import base64

save_path = './'
#文件上传的HTML模板，这里没有额外去写html模板了，直接写在这里，方便点吧
@route('/')
def upload():
    return '''
    <!DOCTYPE HTML>
        <html>
        <head>
        <meta charset="utf-8">
        <title>ET_MAP</title>
        <script src="js/jquery-3.2.1.min.js"></script>
        <style>
        body{margin:0 0}
        .dashboard_target_box {
            width:250px;
            height:105px;
            border:3px dashed #E5E5E5;
            text-align:center;
            top:0;
            left:0;
            cursor:pointer;
            margin:30px auto;
           
        }
        .dashboard_target_box.over {
            border:3px dashed #000;
            background:#ffa
        }
        .dashboard_target_messages_container {
            display:inline-block;
            margin:12px 0 0;
            position:relative;
            text-align:center;
            height:44px;
            overflow:hidden;
            z-index:2000
        }
        .dashboard_target_box_message {
            position:relative;
            margin:4px auto;
            font:15px/18px helvetica, arial, sans-serif;
            font-size:15px;
            color:#999;
            font-weight:normal;
            width:150px;
            line-height:20px
        }
        .dashboard_target_box.over #dtb-msg1 {
            color:#000;
            font-weight:bold
        }
        .dashboard_target_box.over #dtb-msg3 {
            color:#ffa;
            border-color:#ffa
        }
        #dtb-msg2 {
            color:orange
        }
        #dtb-msg3 {
            display:block;
            border-top:1px #EEE dotted;
            padding:8px 24px
        }
        #pic{
            margin:2px auto;
            text-align:center;
        }
        </style>
        <script>
        $(document).ready(function(){

        //设计一段比较流行的滑动样式
                $('#drop_zone_home').hover(function(){
                    $(this).children('p').stop().animate({top:'0px'},200);
                },function(){
                    $(this).children('p').stop().animate({top:'-44px'},200);
                });
                
                
                //要想实现拖拽，首页需要阻止浏览器默认行为，一个四个事件。
                $(document).on({
                    dragleave:function(e){        //拖离
                        e.preventDefault();
                        $('.dashboard_target_box').removeClass('over');
                    },
                    drop:function(e){            //拖后放
                        e.preventDefault();
                    },
                    dragenter:function(e){        //拖进
                        e.preventDefault();
                        $('.dashboard_target_box').addClass('over');
                    },
                    dragover:function(e){        //拖来拖去
                        e.preventDefault();
                        $('.dashboard_target_box').addClass('over');
                    }
                });
                
                //================上传的实现
                var box = document.getElementById('target_box'); //获得到框体
                
                box.addEventListener("drop",function(e){
                    
                    e.preventDefault(); //取消默认浏览器拖拽效果
                    
                    var fileList = e.dataTransfer.files; //获取文件对象
                    //fileList.length 用来获取文件的长度（其实是获得文件数量）
                    
                    //检测是否是拖拽文件到页面的操作
                    if(fileList.length == 0){
                        $('.dashboard_target_box').removeClass('over');
                        return;
                    }
                    //检测文件是不是图片
                    
                    xhr = new XMLHttpRequest();
                    xhr.onload=function(){
                        $("#pic").html(xhr.responseText)
                    }
                    xhr.open("post", "/", true);
                    xhr.setRequestHeader("X-Requested-With", "XMLHttpRequest");
                    
                    var fd = new FormData();
					for(var i in fileList)
						fd.append('data[]',fileList[i]);
                    xhr.send(fd);
                    s=0
                    
                },false);
            
        });
        </script>
        </head>

        <body>
        <div id="target_box" class="dashboard_target_box">
        <div id="drop_zone_home" class="dashboard_target_messages_container">
            <p id="dtb-msg2" class="dashboard_target_box_message" style="top:-44px">选择原始文件<br>
            开始上传</p>
            <p id="dtb-msg1" class="dashboard_target_box_message" style="top:-44px">拖动TXT到<br>
            这里</p>
            </p>
        </div>
        
        </div>


        <div id="pic"></div>
        </body>
        </html>
    '''

@route('/', method = 'POST')
def do_upload():
    #try:
    uploads = request.files.getall('data[]')
    #return "you uploaded {} files. ".format(len(upload))
    #upload.save(save_path,overwrite=True)
    html=[]
    for upload in uploads:
        upload.save(save_path,overwrite=True)
        html.append(parse_file(upload.filename))
    return "<br/>".join(html)
   # except:
     #   return "nok"
        
    
@route('/<name:re:images|css|js>/<path:path>')
def static_img(name,path):
    return static_file(path,root="./"+name)
    
def parse_file(fname):
    m=pd.read_csv(fname,sep=';',header=None,encoding='latin_1',skiprows=3,skipinitialspace=True)        
    m.columns=m.loc[0,:]
    dd=m.iloc[2:,:]
    Qlist=["Q_1(Emi)","V_Inj1(HDA_1)"]
    head=m.loc[0,:]
    Qlabel=head[head.isin(Qlist)][0]
    xd=dd.loc[:,["SendAsapCmd(ASAP)_1","p_Rail(ASAP)",Qlabel]]
    xd['p_Rail(ASAP)'].fillna(method='ffill',inplace=True) 
    xd.dropna(subset=[Qlabel],inplace=True) 
    xd=xd.apply(pd.to_numeric) 
    ff=pd.pivot_table(xd,index='SendAsapCmd(ASAP)_1',columns='p_Rail(ASAP)') 
    ff.columns=ff.columns.droplevel() 
    fig = plt.figure()
    ax = plt.subplot(111)
    plt.title(fname)
    ff.plot(ax=ax,figsize=(8,6)) 
    plt.grid()
    #plt.legend(title="Rail_P. [bar] ").set_visible(True)
    plt.xlabel(r'ET [$\mu$s]')
    plt.ylabel(r'Injected Quantity [mm$^3$/str]')
    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])

    # Put a legend to the right of the current axis
    ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
    #plt.legend(bbox_to_anchor=(1.05, 1), loc=2,mode="expand", borderaxespad=0.)
    s = plt.axes([.16, .6, .28, .24])
    ff.plot(ax=s)
    s.legend_.remove()
    #plt.xticks([])
    #plt.yticks([])
    plt.xlabel("ET").set_visible(False)
    plt.xlim(120, 350)
    plt.ylim(0, 10)

    plt.grid()        
    sio = BytesIO()
    plt.savefig(sio, format='png')
    data = base64.encodebytes(sio.getvalue()).decode()
    #print(data)
    htm = '''
            <img src="data:image/png;base64,{}" />
    '''
    plt.close()
    return htm.format(data)

run(host='0.0.0.0', port=8080, debug=True)