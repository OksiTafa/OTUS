собираем приложение командой:
python -m PyInstaller --onefile --noconsole --name BurnoutTracker main.py

Добавим в автозапуск:
Способ 1. Папка автозагрузки (вручную):                                                                                                                                                                                       
     1. Win + R → shell:startup → Enter                                                                                                                                                                   
     2. Создай там ярлык на BurnoutTracker.exe (ПКМ → Создать ярлык)                                                                                                             
                                                                                                                                                                                                                     
Способ 2. Реестр (можно командой):
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v BurnoutTracker /t REG_SZ /d "C:\путь\к\BurnoutTracker.exe"                                                            
                                                                                                                                                                                                         
Удаление:                                                                                                                                                                                                                                                           
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v BurnoutTracker                                              