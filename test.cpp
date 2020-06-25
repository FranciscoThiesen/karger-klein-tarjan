#include <bits/stdc++.h>
using namespace std;
#define TRACE(x) x
#define WATCH(x) TRACE( cout << #x" = " << x << endl)
#define PRINT(x) TRACE(printf(x))
#define WATCHR(a, b) TRACE( for(auto c = a; c != b;) cout << *(c++) << " "; cout << endl)
#define WATCHC(V) TRACE({cout << #V" = "; WATCHR(V.begin(), V.end()); } )
#define rep(i, a, b) for(int i = a; i < (b); ++i)
#define trav(a, x) for(auto& a : x)
#define all(x) (x).begin(), (x).end()
#define rall(x) (x).rbegin(), (x).rend()
#define sz(x) (int)(x).size()
#define mp make_pair
#define st first
#define nd second

using ll = long long;
using pii = pair<int, int>;
using vi = vector<int>;
using ld = long double;
using pll = pair<ll, ll>;
using vll = vector<ll>;
using pll = pair<ll, ll>;

void buff() { ios::sync_with_stdio( false ); cin.tie( nullptr ); }

constexpr ll MOD = 1e9 + 7;

inline ll pow_mod( ll a, ll b, ll mod = MOD) {
    ll res = 1; a %= mod; assert(b >= 0);
    for(;b;b>>=1) {
        if(b&1) res = (res * a) % mod;
        a = (a * a) % mod;
    }
    return res;
}
// End of template code!
int func(int x) {
    auto b = [&] () {
        auto c = [&] () {
            return v + 1;
        };
        c(x);
    };
    b();
    return x;
}

int main() 
{
    buff();
    
    return 0;
}

