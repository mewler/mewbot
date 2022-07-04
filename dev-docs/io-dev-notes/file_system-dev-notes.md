
### Objective

Generate events on file system changes for input.

Write objects/text out to local files for output (helpful for in bot logging/auditing/archiving).

### Underlying library

[watchfiles][1]

Upsides - fast. Simple.

Downsides - Uses a compiled rust backend which might cause some problems in some edge cases.

### Input

File system events - should be able to monitor individual files and folders separately.

Probably want separate events for files and folders - and for various tasks which could be preformed on them

Files

* Creation - Probably should contain
  * File name
  * Creation time - probably just a unix timestamp for simplicity
  * File size
  * Entire file - should be included as an option - there are some cases where it could be really useful - some cases where it would be better to let the Actions handle their own io. Should probably default to not being included. Default read mode ... just "r" at a guess. But that also needs to be user settable. And in the event so people know
* Deletion
  * File name
  * Deletion time
  * No good way to include file size without a running cache of all file sizes - which could get very large depending on the file system - out of scope. Should be handled by an action if required.
  * No good way to include the entire file without a running cache of all the files in the dir in memory. Suspect this is out of scope.
* Update
  * File name
  * Update time
  * Likewise no way to include the size delta - because of the aforementioned cache issue - so just include size
  * Optionally the current state of the file

Dirs

* Creation
  * Dir name
  * Creation time (unix timestamp as above - in fact - could we standardize to using unix timestamps internally?)
* Update - there are a few different forms an update to a folder could take
  * Folder rename event
    * If this is a rename of the folder being monitored ... then we're going to (probably) loose it - as we don't necessarily know the new name to keep monitoring.
    * Need to check to see if this looks like a delete event
    * rename of an asset in the folder being monitored ... unless this ends up involving a full dir tree traversal every update. In which case, no.
  * Folder delete event
    * And for any asset in this folder

So there seems to be two different operational modes
 * The input class is pointed at a file - in which case it keeps an eye on the file location. If it's deleted, it tells the user, if it's added to, it tells the user. Possibly can't easily tell the difference between a rename and a delete. Will see what the library gives us.
 * The input class is pointed at a folder. So it looks for changes to the contents of the folder.

Don't think it's useful to draw a distinction between if the change is to the sole file monitored or a file in the dir being monitored

### Input events

 - FileCreatedInputEvent
 - FileUpdatedInputEvent - in the future - adding options for owner and permission bit updates? But not in the prototype.
 - FileRenamedInputEvent (might just end up bein a Deleted and a Created)
 - FileDeletedInputEvent
 - DirCreatedInputEvent
 - DirUpdatedInputEvent - when the contents of the folder are updated it'll spew appropriate file events - so this is for when the name of the folder is updated.
 - DirDeletedInputEvent - when the monitored dir - or stuff inside it - is deleted. Note - not sure if we can - or if we want to - also spawn deletion events for all the stuff inside it. This might be preferable, but might also present a considerable technical challenge.

(Names swapped around in the code to create an actually coherent class hierarchy and naming convention - curse you English).

On declaring the file mode in the event dataclass ref this discussion [here][2]. This convinced me to just include the modes in the event dataclass - seemed easier.

### Output events

So this was originally conceived because I just wanted to be able to dump the raw text of discord messages out to disk without having to handle the fileIO in an action. It then occurred that being able to monitor files for input events would be useful - the use case I thought of was causing input events whenever log files where updated.

Bearing in mind that the prototypical use case is just "I want the contents of this message file on disk"

So just supporting file creation - for now.

Also worth being aware of the concerning of infinite loops - writing output files back into the monitored input folder.

Note - some care going to have to be taken with security - something like PyFS - which limits where you can make files and folders - for the moment just forcing people to specify a folder that they want stuff to be created in.
This may be relaxed - with caution - later.

File output events
* Create a file - needs the name of the file and the contents
* Append to a file - the name of the file and the contents
* Overwrite a file - likewise
* Delete a file - just the name of the file to remove should be enough

### The IO Config

Currently, we're defining an input path and an output path. The input path is monitored for input and the output path has output written out to it.

HOWEVER - neither of these are necessary to the function of the other - so if an input_path is not provided, then the IOConfig should not have an input - until such time as a path is provided - which it might be later, on the hoof as it where. But this might screw things up upstream - not sure the framework can cope at present with transitory inputs - so there should always be an input - it should just do nothing until given a sensible thing to monitor.

Would it be best to give it the capacity to monitor multiple different files - or would be best to just force people to define several different IO Configs?

Probably, for simplicity, best for people to define multiple different IO Configs - but that might be a mistake.

### Limitations of the library - or, perhaps, the file system

Watchfiles tells us if a file or folder has been modified - but does not tell us if a file or folder has been changed.

Which probably means that we need to check what the resource is when it's modified ... could just collapse the file and the folder Inputs into a single class ... but that would make the input method a bit less helpful.

Instead - after some research (and some "implementing it badly myself") there are two main options.

[aiofiles][3] - Which has a pathlib built in - but just seems to be a thin wrapper based on running everything in executors - which is not bad, per se, but could be a lot better
[aiopath][4] - Which seems to be a less naive and - probably - more efficient implementation. And also seems capable of handling file io

(Note - there seem to be two different projects - aiofile and aiofiles - file seems better than files, and is included in aiopath as a dependency).

So rolling with aiopath for the moment - may revisit later.

Current we get back a tuple containing the type of change and the path to the changed resource. But not the modification time ... 
Cam retrieve that later ... or just not bother.


NOTE FOR THE FAR FUTURE

I have some vague notions about it being a really good idea if mewbot could (easily) stand being a distributed system. Not for reasons of running many, many bots at once. Not for reasons of scale - we're currently not even really allowing ourselves more than one thread, but for reasons of flexibility. Running some IO methods on linux is looking like a pain.

Or this might be way more trouble than it's worth.

Long story short? You might be surprised when you feel the file_path variable from the IO dataclassess into a local os.path function.
Unexpected behavior may result.

I have the feeling that some IO methods - such as this one - might be a pain in the arse.




[1]: https://github.com/samuelcolvin/watchfiles "Watchfiles"
[2]: https://discuss.python.org/t/enum-for-open-modes/2445/4 "File mode enum discussion"
[3]: https://github.com/Tinche/aiofiles "aiofiles"
[4]: https://github.com/alexdelorenzo/aiopath "aiopath"