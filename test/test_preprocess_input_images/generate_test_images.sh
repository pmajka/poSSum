

# Most of the images are borrowed from the ImageMagick
# documentation website:
#    http://www.imagemagick.org/Usage/canvas/


convert -size 256x256 gradient:'#FFF-#0FF' -rotate 90 \
        -set colorspace HSB -colorspace RGB \
        -quality 80 001_rainbow_gradient_hq.jpg

convert -size 256x256 gradient:'#FFF-#0FF' -rotate 90 \
        -set colorspace HSB -colorspace RGB \
        -quality 10 002_rainbow_gradient_lq.jpg

convert -size 256x256 gradient:'#FFF-#0FF' -rotate 90 \
        -set colorspace HSB -colorspace RGB \
        003_rainbow_gradient.gif

convert -size 256x256 gradient:'#FFF-#0FF' -rotate 90 \
        -alpha set -virtual-pixel Transparent +distort Polar 49 +repage \
        -rotate 90 -set colorspace HSB -colorspace RGB \
        004_gradient_hue_polar.png

echo "P2 2 2 2   2 1 1 0 " | \
     convert - -resize 256x256\! 005_grayscale_1.png


convert xc:black xc:red xc:yellow xc:green1 xc:cyan xc:blue xc:black \
        +append -filter Cubic -resize 256x256\! \
        -rotate 45 -resize 256x256\! \
        -dither Riemersma  -colors 16 \
        006_gradient_limited_nymber_of_colors_16.png

convert xc:red xc:yellow xc:green1 xc:cyan xc:blue \
        +append -filter Cubic -resize 256x256\!  -size 256x256 \
        gradient: +matte -compose CopyOpacity -composite alpha_gradient.png
convert alpha_gradient.png  +dither  -colors 256 007_playing_with_alpha_colors_256.png
convert alpha_gradient.png  +dither  -colors 64  008_playing_with_alpha_colors_64.png
convert alpha_gradient.png  +dither  -colors 15  009_playing_with_alpha_colors_15.png

convert alpha_gradient.png  +dither  -colors 256 011_playing_with_alpha_colors_256.gif
convert alpha_gradient.png  +dither  -colors 64  012_playing_with_alpha_colors_64.gif
convert alpha_gradient.png  +dither  -colors 15  013_playing_with_alpha_colors_15.gif

convert alpha_gradient.png 014_playing_with_alpha_gradient.gif
mv alpha_gradient.png 010_playing_with_alpha_gradient.png

