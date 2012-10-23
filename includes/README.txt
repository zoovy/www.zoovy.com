Stardate: 2009-07-07

The zoovy corporate website has been ravaged over the years by developers
who did not consider the future. Who failed to adhere to good naming 
conventions, who were lazy and did not refactor or rename their files as 
messaging changed.

Eventually the cdn caching became too much, the endless hours of searching
for a css reference embedded in a file that had been lost to the sands of
time.. alas, the pain was too great? Evil men roamed the land, and all 
virtuous maidens ran for cover whenever it became time to update the 
corporate messaging. 

Until one day, there was a light. The instructions below, contains the sacred 
writings which, if followed properly will ensure that mankind will not 
return to the dark ages. 
This file ensures the sacred keepers of the corporate website avoid the peril of the 
easily excitable, and often irriatable "brian". Following these directions,
nay, "scriptures" is the one and only way to protect yourself from the evil
which lurks outside your door.

Abandon all faith, ye of little hope. 

-----------------------------------------------------------------------------
ZOOVY CORPORATE WEBSITE DEVELOPER GUIDELINES
-----------------------------------------------------------------------------


ZOOVY USES MASON:
Mason can be used for good or evil depending on who wields it's power. 
http://www.masonbook.com/book/



DATES:
All dates incorporated in files will be stored in the format YYYYMMDD, 
and without exception will appear the end of a filename. Dates, while 
annoying, help preserve the historical archive and also generally make 
it blinding obvious when old content is being referenced. 


REWRITES:
to fix some old bad naming conventions there are rewrites at the upper layer
e.g. /amazon will auto-redirect to /compatible-integration-review/amazon
this is really useful from SEO perspective, but you can still give out
/amazon


NAMING CONVENTIONS:
Pushing, or requesting push of code which does not follow our naming
conventions will be dealt with in an unpleasant manner. Naming conventions
are not for you, they are for future you. Trust me - future you will 
absolutely appreciate it. 
Following naming conventions also appeases the volcano gods, which keeps 
them at bay.

SEO:
Do not create duplicate content on pages.
Always use alt tags. ALWAYS SET GOOD SEO FRIENDLY TITLE TAGS.
Think about your urls .. don't write "shipwithfedex" instead use "ship-with-fedex"
Never symlink CONTENT, it's a bad idea because it will lead to duplicates .. use a 301 instead.
Keep the pages fresh, incorporate "dates" which automatically update (Mason)
there are lots of ways to do this -- but here is one example:
<%perl> use Date::Calc; my @today  = Date::Calc->Today(); print "$today[0]-$today[1]-$today[2]"; </%perl>

Google's algorithms rank pages which update frequently, but aren't dynamic (different each
time), they'll check a page, and then check back in a few hours or days to see if the page has changed. 

Have content on the pages which cycles, but cycle with a 1 day period so Google 
doesn't decide it's dynamic. For example using an array of 10 elements (@PDFS for 
example), we want to only show 8 of the pdfs.
	my $show = scalar(@PDFS)-2;						## always show N-2 PDF's.
	my $pos = ((time()%86400)%scalar(@PDFS));		## randomly picks a new starting position every day.
	if (($pos+$show)>scalar(@PDFS)) {
		## if the starting position ($pos) + the number to show, is greater than the 
		## number of @pdfs we have, then we'd run over. So we'll append the array to itself.
		@PDFS = (@PDFS,@PDFS);			
		}
	@PDFS = splice(@PDFS,$pos,$show);
	## now we use our loop to show @PDFS

only show 8 of the pdfs  use (time()%86400)


PDFS:
PDF's are SEO dynamite. Google loves PDFs. PDF's should be written with SEO in mind
(but not overly optimized for SEO).



DIRECTORY STRUCTURE: 
/biz
/webapi 
/login
/webdoc
/recover	- these are sacred ground, do not touch.

/images	-	using this directory will only further demonstrate your ignorance.

/includes/	-	includes all shared assets utilized by the website.
	"Assets" are corporate intellectual property, and should be regarded as such.
	Assets should be given their own directory which denotes what their "role" in 
	the website is, and some indicator of their content along with a date

	Assets are reusable, meaning they are used throughout the site.

	Examples of asset naming:
	/header-20090707							- the header for the 20090707 website
	/footer-20090707							- the footer for the 20090707 website
	/homepage-20090707						- resource files for the homepage
	/panel-seven_areas_wheel-20090707	- a "panel" which contains about the "seven areas wheel"
	/embedbar-howitworks-20090707			- an embeddable bar which describes "how it works"
	
	Whenever possible assets names should be agreed upon prior to creation of an asset, prior
	to the commencement of the creation of an asset.
	
	Each asset directory should include a "index.html" -- this should ALWAYS render
	a valid w3c html code snippet. E.g. never start with a <tr> or fail to close a </table>

	Each asset should include an HTML comment at the start and stop. ex:
	<!-- BEGIN /includes/embedbar-howitworks-20090707 -->
	<!-- END /includes/embedbar-howitworks-20090707 -->

/includes/header/index.html
/includes/footer/index.html
	these are both symbolic links, which means they are pointers to the current header	
	and footer respectively. If you need to update them, you'll need a sysop. 
	You should NEVER change an existing header or footer, rather, create a new copy with a 
	new date / time, if you don't do this, the caching gods will punish you and the volcano
	gods will smite you.

	** note the files IN the header should always reference full paths meaning 
	inside the file you'd reference /includes/header-20090707/path_to_graphic-XXxYY.png

/includes/track.html - things you need to know: 
	1. the arcane runes in this file are scriptures maintained by the great volcano god. 
	2. It ensures proper ROI tracking across both present and historical sites.
	3. this file MUST be called before any output in /includes/header/index.html
	4. if you don't call /includes/header/index.html for some unknown reason -- then you
		not only a coward, but if you don't include track.html you are also a fool who shall
		receive no mercy at the feet of the volcano god.

	** this file also contains a blessing for any person who is creating inbound links to the site.

/partnername 
	example:
		/amazon
		/ups
		/fedex
	.. they don't actually exist, they are redirected in /track.html
	these are 301 redirected to /compatible-integration-review/partner for SEO reasons.
	when somebody searches for "buysafe review" .. I want Zoovy to rank (so does buysafe)
	the mapping is done in a hash contained in: /httpd/modules/SITE/Mason.pm
	regrettably we can't make this easier.




Creating new pages

If the page is a new tier1 (like products, company, partners, etc) then it should be it's own folder.  All sub-nav for it should be an appropriately named .html file within that directory.

If a new page is going to have several 'sub' pages that are releated, create it as a folder with an index.html and each of the subpages should be appropriately named .html files within that directory. example would be company/employment/




Symlinking help for includes.

rm footer
ln -s footer-20100825 footer

301 redirects can be set up here:
First, create a backup of this file:
/httpd/modules/SITE/Mason.pm
then edit and push

