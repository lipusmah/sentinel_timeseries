
REM Requires python 3.6.* to be in PATH
python -m virtualenv env

REM Activate created env
CALL .\env\Scripts\activate

REM Installing prebuild Shapely
pip install assets\Shapely-1.6.4.post1-cp36-cp36m-win_amd64.whl

