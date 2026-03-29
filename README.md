# Chapterize

An improvement on [JonathanReeve](github.com/JonathanReeve)'s Chapterize repo that allows you to split ebooks into their chapters as .txt files and create a PDF of all of the images that are in the book, appending them at the end of the file. Optimal for LLM and book analysis. 

## Usage

run the following command to try:
```
python3 chapterize/epub_chapterize.py **{filepath/to/book.epub}** --verbose 2>&1
```



### Break a Novel into Chapters: 

```
# Grab a copy of Pride and Prejudice from Project Gutenberg: 
wget https://www.gutenberg.org/files/1342/1342-0.epub

# Give it a nicer name. 
mv {crazy title}.epub -> pride-and-prejudice.txt 

# Run EPUB Chapterize on it:  
chapterize python3 chapterize/epub_chapterize.py pride-and-prejudice.txt --verbose 2>&1
```

This should output a directory in the current working directory called `pride-and-prejudice`, containing files pride-and-prejudice-01.txt through pride-and-prejudice-56.txt. There will also be a PDF attached with all of the figures. 


## Installation 

Chapterize is now on PyPi, installable with `pip`. You can install it with: 

```
sudo pip3 install chapterize
```

Or, to get the very latest version from GitHub, run: 

```
git clone https://github.com/JonathanReeve/chapterize.git
cd chapterize
sudo pip3 install .
```

## State

This tool is in a pre-alpha state. There are a lot of types of chapter headings it can’t recognize.

## Contributing

Pull requests welcome!
