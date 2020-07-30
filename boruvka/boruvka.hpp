#ifndef BORUVKA_H
#define BORUVKA_H

#include <vector>
#include <utility>

using namespace std;

vector< tuple<int, int, int> > boruvka(const vector< tuple<int, int, int> >& edges, int n);

#endif
