# procrustes

things to remember: 

  * there is a file being ignored by the repo that you MUST HAVE:

      ROOT/startup.m

    should contain the following line:

      run('/Users/valkyrie/libraries/vlfeat-0.9.20/toolbox/vl_setup')

    (with appropriate path - download vlfeat from http://www.vlfeat.org/install-matlab.html)

  * if the ./triCheck executable doesnt work, compile the .cpp with g++ -std=c++11  -o triCheck triCheck.cpp

  * tags to be checked should be .jpgs in the /tags folder in the home directory. tags need to be in RGB color space, rather than CMYK

  * obj file and its associated texture .jpgs and .mtl should be in the /obj folder in the home directory
 
  * sudo pip install enum34 if python says enum isn't found
Notes on installing this!

