package uk.me.csudcy.bletr;

import android.content.SharedPreferences;
import android.os.Bundle;
import android.preference.EditTextPreference;
import android.preference.Preference;
import android.preference.PreferenceActivity;
import android.text.InputType;

public class SettingsActivity extends PreferenceActivity implements
        SharedPreferences.OnSharedPreferenceChangeListener {
    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        addPreferencesFromResource(R.xml.pref_general);

        // Set all summaries manually
        SharedPreferences sp = getPreferenceScreen().getSharedPreferences();
        for (String key : sp.getAll().keySet()) {
            updatePrefSummary(key);
        }
    }

    protected void onResume() {
        super.onResume();
        getPreferenceScreen().getSharedPreferences()
                .registerOnSharedPreferenceChangeListener(this);
    }

    protected void onPause() {
        super.onPause();
        getPreferenceScreen().getSharedPreferences()
                .unregisterOnSharedPreferenceChangeListener(this);
    }

    public void onSharedPreferenceChanged(SharedPreferences sharedPreferences, String key) {
        updatePrefSummary(key);
    }

    private void updatePrefSummary(String key) {
        Preference pref = findPreference(key);
        if (pref instanceof EditTextPreference) {
            EditTextPreference etp = (EditTextPreference) pref;
            String summaryText = etp.getText();
            if ((etp.getEditText().getInputType() & InputType.TYPE_TEXT_VARIATION_PASSWORD) != 0) {
                // TODO: Make this similar to (but not exactly) the password length
                summaryText = "**********";
            }
            pref.setSummary(summaryText);
        }
    }
}
