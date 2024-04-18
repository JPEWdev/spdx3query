# spdx3query
Command line tool for querying SPDX 3 files

## Installation

`spdx3query` can be installed using `pip`:

```shell
python3 -m pip install spdx3query
```

## Usage

`spdx3query` takes one or mode SPDX 3 JSON files as input using the `-i` option
and then a subcommand to query information about it. For example, this command
will list all `Build` objects found in `my-sdpx.spdx.json`:

```shell
spdx3query -i my-spdx.spdx.json find --type build_Build
```

There are many commands that `spdx3query` supports. For a list of commands, see
`spdx3query --help`. Each command also implements a `--help` which can provide
additional information about what it does, for example `spdx3query find --help`

### Interactive mode

In addition to the top level subcommands of `sdpx3query`, there is also an
interactive mode where commands can be run. This can be useful for
interactively exploring SPDX 3 files, particularly if they are very large as
the dataset only needs to be loaded once. To enter interactive mode, the
`interactive` subcommand is used, for example:

```shell
spdx3query -i my-spdx.spdx.json interactive
```

From the prompt, any query subcommand can be run in the same way as if it had
been specified on the command line, for example:

```
> find --type build_Build
```

### Object Mnemonic Handles

Objects in SPDX 3 are often assigned IRIs as identifiers (either in the `@id`
or `spdxId` property, depending on the object). These IRI names are often very
long and can be difficult to type in correctly when performing queries on a
data file. To aid in identifying objects, `spdx3query` assigns a mnemonic to
each device that can be used in place of the identifier. The mnemonic uses
words from the [BIP 39][1] word list, and by default uses 3 terms. If you are
dealing with a large datafile, you can increase the number of terms using the
`--handle-terms` argument to `spdx3query`. The mnemonic handle is based on a
hash of the actual ID, and therefore is stable even when loading the same file
multiple times.

As an example, you can see the mnemonic handle for the following build object
is "chest-acoustic-phone"

```
$ spdx3query -i bitbake.spdx.json find --type build_Build --show
Loaded 18 objects in 0.01s
Found 1 object(s):

build_Build - 'chest-acoustic-phone'
  spdxId: 'http://spdx.org/spdxdoc/bitbake-addba517-4804-5ae3-87c2-0c3a1a5812ba/bitbake/2ae7c23f5bf50e79d5c97b3a3f2294bb'
```

This means that you can can use this mnemonic handle in place of the actual
spdxId to reference this object, e.g.:

```shell
spdx3query -i bitbake.spdx.json show chest-acoustic-phone
```

For objects that do not have an ID, a mnemonic handle will also be assigned,
but it will have a `LOCAL-` prefix prepended to it. These handles are not
guaranteed to remain the same between different invocations of `spdx3query`.
For example:

```
$ spdx3query -i bitbake.spdx.json find --type CreationInfo
Loaded 18 objects in 0.01s
Found 1 object(s):
CreationInfo - 'LOCAL-stereo-window-riot'
```

## Development

Development on `spdx3query` can be done by setting up a virtual environment and
installing it in editable mode:

```shell
python3 -m venv .venv
. .venv/bin/activate
pip install -e .[dev]
```

Tests can be run using pytest:

```shell
pytest -v
```

[1]: https://github.com/bitcoin/bips/blob/master/bip-0039.mediawiki
