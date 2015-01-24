package uk.me.csudcy.bletr;

/*
BLEtr
-----

Monitor beacons in the local area and send the information back to the BELtr server

TODO:
  Don't lose events if sending fails
  Improve background running
  Persist events to disk

DONE:
  Record events locally and batch send them to server
  Persist server details
  Move server details to a settings page
 */

import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Looper;
import android.os.RemoteException;
import android.preference.PreferenceManager;
import android.support.v7.app.ActionBarActivity;
import android.os.Bundle;
import android.util.Log;
import android.view.Menu;
import android.view.MenuInflater;
import android.view.MenuItem;
import android.widget.CompoundButton;
import android.widget.Switch;
import android.widget.TextView;
import android.widget.Toast;

import org.altbeacon.beacon.Beacon;
import org.altbeacon.beacon.BeaconConsumer;
import org.altbeacon.beacon.BeaconManager;
import org.altbeacon.beacon.BeaconParser;
import org.altbeacon.beacon.RangeNotifier;
import org.altbeacon.beacon.Region;
import org.altbeacon.beacon.powersave.BackgroundPowerSaver;

import java.util.Collection;

// See https://altbeacon.github.io/android-beacon-library/samples.html

public class MainActivity extends ActionBarActivity implements BeaconConsumer, RangeNotifier {
    protected static final String TAG = "MainActivity";
    private BeaconManager beaconManager = BeaconManager.getInstanceForApplication(this);
    private Region allRegions = new Region("myRangingUniqueId", null, null, null);
    // Simply constructing this class and holding a reference to it in your custom Application class
    // enables auto battery saving of about 60%
    private BackgroundPowerSaver backgroundPowerSaver = new BackgroundPowerSaver(this);

    // Trackers to track various beacon information
    private BeaconTracker beaconTracker;
    private EventTracker eventTracker;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        // Load default preferences
        PreferenceManager.setDefaultValues(this, R.xml.pref_general, false);

        // Initialise trackers
        beaconTracker = new BeaconTracker(this);
        eventTracker = new EventTracker(this);

        // Add parser for iBeacons
        // See http://stackoverflow.com/questions/25027983/is-this-the-correct-layout-to-detect-ibeacons-with-altbeacons-android-beacon-li
        beaconManager.getBeaconParsers().add(new BeaconParser().setBeaconLayout("m:2-3=0215,i:4-19,i:20-21,i:22-23,p:24-24"));

        // Initialise the beaconManager
        beaconManager.bind(this);

        // Bind to monitor switch
        Switch monitorSwitch = (Switch) findViewById(R.id.monitorSwitch);
        monitorSwitch.setOnCheckedChangeListener(
                new CompoundButton.OnCheckedChangeListener() {
                    public void onCheckedChanged(CompoundButton buttonView, boolean isChecked) {
                        setMonitoringEnabled(isChecked);
                    }
                }
        );

        // Show the initial status
        updateStatus();
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();

        // Kill the beaconManager
        beaconManager.unbind(this);
    }

    @Override
    public boolean onCreateOptionsMenu(Menu menu) {
        MenuInflater inflater = getMenuInflater();
        inflater.inflate(R.menu.menu_main, menu);
        return true;
    }

    @Override
    public void onBeaconServiceConnect() {
        beaconManager.setRangeNotifier(this);
    }

    @Override
    public void didRangeBeaconsInRegion(Collection<Beacon> beacons, Region region) {
        // Iterate over beacons to update trackers
        for (Beacon beacon : beacons) {
            beaconTracker.updateBeacon(beacon);
            eventTracker.addEvent(beacon);
        }

        updateStatus();
    }

    public void updateStatus() {
        // This must be run from the UI thread
        if (Looper.myLooper() != Looper.getMainLooper()) {
            runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    updateStatus();
                }
            });

            return;
        }

        // We are definitely on the UI thread now
        TextView beaconStatusText = (TextView) findViewById(R.id.beaconStatusText);
        beaconStatusText.setText(beaconTracker.toString());

        TextView eventStatusText = (TextView) findViewById(R.id.eventStatusText);
        eventStatusText.setText(eventTracker.toString());
    }

    public void setMonitoringEnabled(boolean enabled) {
        TextView beaconStatusText = (TextView) findViewById(R.id.beaconStatusText);
        if (enabled) {
            // Monitoring is enabled
            try {
                beaconManager.startRangingBeaconsInRegion(allRegions);
            } catch (RemoteException e) {
                beaconStatusText.setText(
                        getString(
                                R.string.main__monitoring_error,
                                e.toString()
                        )
                );
            }
        } else {
            // Monitoring is disabled
            try {
                beaconManager.stopRangingBeaconsInRegion(allRegions);
            } catch (RemoteException e) {
                beaconStatusText.setText(
                        getString(
                                R.string.main__monitoring_error,
                                e.toString()
                        )
                );
            }
        }
    }

    public void showSettings(MenuItem menu) {
        startActivity(new Intent(this, SettingsActivity.class));
    }

    public void toastMessage(String msg, int duration) {
        // This must be run from the UI thread
        if (Looper.myLooper() != Looper.getMainLooper()) {
            final String msgCopy = msg;
            final int durationCopy = duration;
            runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    toastMessage(msgCopy, durationCopy);
                }
            });

            return;
        }

        // We are definitely on the UI thread now
        Toast.makeText(
                this,
                msg,
                duration
                //Toast.LENGTH_LONG
        ).show();
    }
}
