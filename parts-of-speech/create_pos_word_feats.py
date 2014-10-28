import re
import time
import io
import sys
import argparse
from collections import defaultdict

# parse/validate arguments
argParser = argparse.ArgumentParser()
argParser.add_argument("-b", "--brown_filename")
argParser.add_argument("-o", "--output_filename")
argParser.add_argument("-hk", "--haghighi_klein", action='store_true', help='when set, only use features used by Haghighi and Klein 2006, and later by Berg-Kirkpatrick et al 2010. By default, use the "full" set of features, as detailed in Ammar et al. 2014')
args = argParser.parse_args()

brown_file = io.open(args.brown_filename, encoding='utf8', mode='r')
output_file = io.open(args.output_filename, encoding='utf8', mode='w')

digit_regex = re.compile('\d')
hyphen_regex = re.compile('-')

suffix_counts = defaultdict(int)
counter = 0
for line in brown_file:
  counter += 1
  splits = line.split('\t')
  if len(splits) != 3:
    print 'len(splits) = ', len(splits), ' at line ', counter
    print splits
    assert False
  cluster, word, frequency = splits
  for suffix_length in range(1,4):
    if len(word) > suffix_length:
      suffix_counts[word[-suffix_length:]] += 1

## This is the value "f" in Table 2 of Ammar et al. 2014
min_suffix_count = 1 if args.haghighi_klein else 10

brown_file.close()
brown_file = io.open(args.brown_filename, encoding='utf8', mode='r')
for line in brown_file:
  cluster, word, frequency = line.split('\t')
  frequency = int(frequency)
  
  features = {
#    u'cluster-{}'.format(cluster):1, 
#    u'clus-{}'.format(cluster[0:4]):1
    }
  
  # suffixes
  for suffix_length in range(1,4):
    if len(word) > suffix_length and suffix_counts[word[-suffix_length:]] > min_suffix_count:
      features[u'{}-suff-{}'.format(suffix_length, word[-suffix_length:])]=1

  # hypthen
  if hyphen_regex.search(word):
    features[u'contain_hyphen'] = 1

  # alphanumeric
  if digit_regex.search(word):
    features[u'contain_digit'] = 1
  if not args.haghighi_klein:
    if word.isdigit():
      features[u'number'] = 1
    elif word.isalpha():
      features[u'word'] = 1
    elif word.isalnum():
      features[u'alphanumeric'] = 1
    else:
      features[u'nonalphanumeric'] = 1

  # case
  if word.islower():
    features[u'lower'] = 1
  elif word.isupper():
    features[u'upper'] = 1
  elif word[0].isupper():
    features[u'upper-initial'] = 1

  # word string
  min_lowercased_frequency = 11
  if frequency >= min_lowercased_frequency:
    features[u'lower_{}'.format(word.lower()).replace(u'=', u'eq')] = 1
  if args.haghighi_klein:
    features[word.replace(u'=', u'eq')] = 1

  # word shape
  if not args.haghighi_klein:
    shape=[u'^']
    for c in word:
      if c.isdigit():
        if shape[-1] != u'0': shape.append(u'0')
      elif c.isalpha() and c.islower():
        if shape[-1] != u'a': shape.append(u'a')
      elif c.isalpha() and c.isupper():
        if shape[-1] != u'A': shape.append(u'A')
      else: 
        if shape[-1] != u'#': shape.append(u'#')
    features[u''.join(shape)] = 1
  
  if len(features) == 0: 
    continue

  output_file.write(u'{} ||| {} |||'.format(word, word))
  for featureId in features.keys():
    output_file.write(u' {}={}'.format( featureId, features[featureId] ) )
  output_file.write(u'\n')

output_file.close()
brown_file.close()
