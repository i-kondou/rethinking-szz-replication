This repository contains a bug that was introduced at some point in the past
and later fixed. Below is the bug-fixing commit information.

Your task is to identify the commit(s) that introduced the bug, and explain
your reasoning.

[Bug-Fixing Commit]
- Commit hash: 273b473f8706e1c8c8633539f6436c4285559604
- Commit message: 
- Diff:
```
commit 273b473f8706e1c8c8633539f6436c4285559604
Author: Vinícius <computationalcore@gmail.com>
Date:   Thu Feb 16 21:24:36 2017 -0200
---
 .../adapters/TransfersTableAdapter.java             | 21 +++++++--------------
 .../fragments/BalancesFragment.java                 |  2 +-
 2 files changed, 8 insertions(+), 15 deletions(-)

diff --git a/app/src/main/java/de/bitshares_munich/adapters/TransfersTableAdapter.java b/app/src/main/java/de/bitshares_munich/adapters/TransfersTableAdapter.java
index 134eb82..b9cad9f 100644
--- a/app/src/main/java/de/bitshares_munich/adapters/TransfersTableAdapter.java
+++ b/app/src/main/java/de/bitshares_munich/adapters/TransfersTableAdapter.java
@@ -9,9 +9,7 @@ import android.view.ViewGroup;
 import android.widget.ImageView;
 import android.widget.TextView;
 
-import java.text.NumberFormat;
 import java.text.SimpleDateFormat;
-import java.util.Currency;
 import java.util.Date;
 import java.util.Locale;
 import java.util.TimeZone;
@@ -19,6 +17,8 @@ import java.util.regex.Matcher;
 import java.util.regex.Pattern;
 
 import de.bitshares_munich.database.HistoricalTransferEntry;
+import de.bitshares_munich.models.Smartcoins;
+import de.bitshares_munich.smartcoinswallet.Constants;
 import de.bitshares_munich.smartcoinswallet.R;
 import de.bitshares_munich.utils.Helper;
 import de.bitsharesmunich.graphenej.AssetAmount;
@@ -35,12 +35,10 @@ public class TransfersTableAdapter extends TableDataAdapter<HistoricalTransferEn
     private String TAG = this.getClass().getName();
 
     private UserAccount userAccount;
-    private Locale locale;
 
-    public TransfersTableAdapter(Context context, Locale locale, UserAccount userAccount, HistoricalTransferEntry[] data) {
+    public TransfersTableAdapter(Context context, UserAccount userAccount, HistoricalTransferEntry[] data) {
         super(context, data);
         this.userAccount = userAccount;
-        this.locale = locale;
     }
 
     @Override
@@ -143,8 +141,8 @@ public class TransfersTableAdapter extends TableDataAdapter<HistoricalTransferEn
         TextView fiatAmountTextView = (TextView) root.findViewById(R.id.fiat_amount);
         AssetAmount smartcoinAmount = historicalTransfer.getEquivalentValue();
 
-//        String language = Helper.fetchStringSharePref(getContext(), getContext().getString(R.string.pref_language), Constants.DEFAULT_LANGUAGE_CODE);
-//        Locale locale = new Locale(language);
+        String language = Helper.fetchStringSharePref(getContext(), getContext().getString(R.string.pref_language), Constants.DEFAULT_LANGUAGE_CODE);
+        Locale locale = new Locale(language);
         String symbol = "";
         if(transferAmount.getAsset() != null){
             symbol = transferAmount.getAsset().getSymbol();
@@ -169,13 +167,8 @@ public class TransfersTableAdapter extends TableDataAdapter<HistoricalTransferEn
         }
 
         if(smartcoinAmount != null){
-            Log.d(TAG,"Using smartcoin: "+smartcoinAmount.getAsset().getObjectId());
-            final Currency currency = Currency.getInstance(smartcoinAmount.getAsset().getSymbol());
-            NumberFormat currencyFormatter = Helper.newCurrencyFormat(getContext(), currency, locale);
-            String eqValue = currencyFormatter.format(Util.fromBase(smartcoinAmount));
-
-//            String fiatSymbol = Smartcoins.getFiatSymbol(smartcoinAmount.getAsset());
-//            String eqValue = String.format("~ %s %.2f", fiatSymbol, Util.fromBase(smartcoinAmount));
+            String fiatSymbol = Smartcoins.getFiatSymbol(smartcoinAmount.getAsset());
+            String eqValue = String.format("~ %s %.2f", fiatSymbol, Util.fromBase(smartcoinAmount));
             fiatAmountTextView.setText(eqValue);
         }else{
             Log.w(TAG, String.format("Fiat amount is null for transfer: %d %s", transferAmount.getAmount().longValue(), transferAmount.getAsset().getSymbol()));
diff --git a/app/src/main/java/de/bitshares_munich/fragments/BalancesFragment.java b/app/src/main/java/de/bitshares_munich/fragments/BalancesFragment.java
index 8d5b38b..71622af 100644
--- a/app/src/main/java/de/bitshares_munich/fragments/BalancesFragment.java
+++ b/app/src/main/java/de/bitshares_munich/fragments/BalancesFragment.java
@@ -2549,7 +2549,7 @@ public class BalancesFragment extends Fragment implements AssetDelegate, ISound,
             }
 
         }else{
-            tableAdapter = new TransfersTableAdapter(getContext(), locale, account, newData.toArray(new HistoricalTransferEntry[newData.size()]));
+            tableAdapter = new TransfersTableAdapter(getContext(), account, newData.toArray(new HistoricalTransferEntry[newData.size()]));
             transfersView.setDataAdapter(tableAdapter);
         }
```

Investigate the repository using local tools. Do not use web search.

When you have identified the bug-introducing commit(s), conclude your
response with the following two sections:

## Bug-Introducing Commits
BIC: <hash1>, <hash2>, ... (or "BIC: NONE")

## Reasoning
Explain:
(1) How you investigated and what led you to this candidate.
(2) What specific change in this commit you believe introduced the bug.
(3) What evidence in the repository supports this conclusion.

Be honest about uncertainty if any.
