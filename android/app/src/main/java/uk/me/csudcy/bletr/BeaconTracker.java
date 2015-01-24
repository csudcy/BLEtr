package uk.me.csudcy.bletr;

import android.content.Context;
import android.text.format.DateUtils;

import org.altbeacon.beacon.Beacon;

import java.util.ArrayList;
import java.util.Date;

/**
 * Created by csudcy on 25/12/2014.
 */
public class BeaconTracker {
    Context ctx;

    class BeaconData {
        private Beacon beacon;
        private double distance;
        private Date lastSeen;

        public BeaconData(Beacon beacon) {
            this.beacon = beacon;
            this.distance = beacon.getDistance();
            this.lastSeen = new Date();
        }

        public boolean checkAndUpdate(Beacon beacon) {
            if (!beacon.equals(this.beacon)) {
                return false;
            }

            this.distance = beacon.getDistance();
            this.lastSeen = new Date();
            return true;
        }

        @Override
        public String toString() {
            return ctx.getString(
                    R.string.beacontracker__beacon_result,
                    beacon.getId3().toHexString(),
                    distance,
                    DateUtils.getRelativeTimeSpanString(
                            lastSeen.getTime(),
                            new Date().getTime(),
                            1000
                    )
            );
        }
    }

    private ArrayList<BeaconData> beacons = new ArrayList<BeaconData>();

    public BeaconTracker(Context ctx) {
        this.ctx = ctx;
    }

    public void updateBeacon(Beacon beacon) {
        for (BeaconData seenBeacon : beacons) {
            if (seenBeacon.checkAndUpdate(beacon)) {
                return;
            }
        }

        // This is a new beacon
        beacons.add(new BeaconData(beacon));
    }

    @Override
    public String toString() {
        if (beacons.size() == 0) {
            return ctx.getString(R.string.beacontracker__no_beacons);
        }

        // Iterate over beacons to construct the status output
        String beaconResults = "";
        for (BeaconData seenBeacon : beacons) {
            beaconResults += seenBeacon.toString() + "\n\n";
        }
        return beaconResults;
    }
}
