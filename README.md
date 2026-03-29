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
wget https://cdn.mises.org/principles_of_economics.epub

# (if needed) give it a nicer name. 
mv {crazy title}.epub principles_of_economics.epub 

# Run EPUB Chapterize on it:  
chapterize python3 chapterize/epub_chapterize.py principles_of_economics.epub --verbose 2>&1
```

This should output a directory in the current working directory called `principles_of_economics`, containing files principles_of_economics-01-Cover.txt through principles_of_economics-18-Index.txt. There will also be a PDF attached with all of the figures, principles_of_economics-images.pdf. 


## Installation 

To get the this version, run: 

```
git clone https://github.com/seth-mc/chapterize.git
cd chapterize
sudo pip3 install .
```

## State

This tool is in a pre-alpha state. It now uses the epub structure to deliate the sections, output as .txt files. If you are finding an epub that isn't structred with chapters, it might pull in the book differently than you'd expect.

## Contributing

Pull requests welcome!
