cd ~\Desktop\Plugins-Dev\EndStone\Projects\endstone-easycheckupdate\
Remove-Item '.\dist\*' -Recurse
Remove-Item '.\build\*' -Recurse
Remove-Item '.\src\endstone_easycheckupdate.egg-info' -Recurse
python .\setup.py sdist build
pipx run build --wheel
cd ~\Desktop\Plugins-Dev\Endstone\
Remove-Item 'C:\Users\HeYuHan\Desktop\Plugins-Dev\Endstone\bedrock_server\plugins\endstone_easycheckupdate*.whl'
Copy-Item -Path 'C:\Users\HeYuHan\Desktop\Plugins-Dev\EndStone\Projects\endstone-easycheckupdate\dist\end*.whl' -Destination 'C:\Users\HeYuHan\Desktop\Plugins-Dev\Endstone\bedrock_server\plugins'
# cls
start .\start.cmd