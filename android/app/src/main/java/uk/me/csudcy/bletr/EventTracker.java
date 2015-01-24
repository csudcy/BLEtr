package uk.me.csudcy.bletr;

import android.app.Activity;
import android.content.Context;
import android.content.SharedPreferences;
import android.net.http.AndroidHttpClient;
import android.os.AsyncTask;
import android.preference.PreferenceManager;
import android.text.TextUtils;
import android.util.Log;
import android.widget.Toast;

import com.google.gson.Gson;

import org.altbeacon.beacon.Beacon;
import org.altbeacon.beacon.Identifier;
import org.apache.http.Header;
import org.apache.http.HttpEntity;
import org.apache.http.HttpResponse;
import org.apache.http.NameValuePair;
import org.apache.http.client.entity.UrlEncodedFormEntity;
import org.apache.http.client.methods.HttpPost;
import org.apache.http.impl.client.DefaultHttpClient;
import org.apache.http.message.BasicNameValuePair;
import org.apache.http.params.BasicHttpParams;
import org.apache.http.params.HttpConnectionParams;
import org.apache.http.params.HttpParams;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.io.UnsupportedEncodingException;
import java.util.ArrayList;
import java.util.Calendar;
import java.util.Date;
import java.util.List;
import java.util.concurrent.Executor;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * Created by csudcy on 25/12/2014.
 */
public class EventTracker {
    class Event {
        private String id;
        private double distance;
        private long timestamp;

        public Event(Beacon beacon) {
            this.id = TextUtils.join("::", beacon.getIdentifiers());
            this.distance = beacon.getDistance();
            this.timestamp = System.currentTimeMillis() / 1000;
        }
    }

    class EventReporter extends AsyncTask<ArrayList<Event>, Void, Void> {
        @Override
        protected Void doInBackground(ArrayList<Event>[] eventsToSendList) {
            if (eventsToSendList.length != 1) {
                throw new IllegalArgumentException("EventReporter should only be called with exactly 1 ArrayList<Event>!");
            }
            ArrayList<Event> eventsToSend = eventsToSendList[0];

            // JSON encode the events to send to the BLEtr server
            Gson gson = new Gson();
            String event_json = gson.toJson(eventsToSend);

            // Construct the URl we will post to
            String url = preferences.getString("report_server", null);
            if (!url.startsWith("http")) {
                url = "http://" + url;
            }
            if (!url.endsWith("/")) {
                url += "/";
            }
            url += "report/";
            Log.d("EventTracker", "Posting report to " + url);

            // Create our POST request
            HttpPost request = new HttpPost(url);
            List<NameValuePair> postData = new ArrayList<NameValuePair>(2);
            postData.add(
                    new BasicNameValuePair(
                            "login_username",
                            preferences.getString("report_username", null)
                    )
            );
            postData.add(
                    new BasicNameValuePair(
                            "login_password",
                            preferences.getString("report_password", null)
                    )
            );
            postData.add(
                    new BasicNameValuePair(
                            "events",
                            event_json
                    )
            );

            // Setup our http client
            HttpParams httpParameters = new BasicHttpParams();
            // Set the timeout in milliseconds until a connection is established.
            HttpConnectionParams.setConnectionTimeout(httpParameters, 5000);
            // Set the default socket timeout in milliseconds which is the timeout for waiting for data.
            HttpConnectionParams.setSoTimeout(httpParameters, 5000);
            DefaultHttpClient httpClient = new DefaultHttpClient(httpParameters);

            // Send the JSON to the BLEtr server
            try {
                UrlEncodedFormEntity encodedPostData = new UrlEncodedFormEntity(postData);
                request.setEntity(encodedPostData);

                // Execute HTTP Post Request
                HttpResponse response = httpClient.execute(request);
                Log.d("EventTracker", "response: " + response.getStatusLine());
            } catch (Exception e) {
                // Log everything!
                Log.d("EventTracker", "Error sending events to server:");
                e.printStackTrace();

                // Toast the error message
                MainActivity ma = (MainActivity) ctx;
                ma.toastMessage(
                        "Error sending events to server: " + e.toString(),
                        Toast.LENGTH_LONG
                );

                // Add all the events back to the queue to get sent to the server & update UI
                events.addAll(eventsToSend);
                ma.updateStatus();
            }

            return null;
        }
    }

    private Context ctx;
    private AtomicInteger totalEventCount = new AtomicInteger(0);
    private ArrayList<Event> events = new ArrayList<Event>();
    private SharedPreferences preferences;
    private Date earliestNextReport = new Date();

    public EventTracker(Context ctx) {
        this.ctx = ctx;
        preferences = PreferenceManager.getDefaultSharedPreferences(ctx);
    }

    private boolean shouldReportNow() {
        // Do we have enough events to report now?
        if (events.size() < preferences.getInt("report_interval", -1))
            return false;
        // Has it been long enough since the previous report?
        if (new Date().before(earliestNextReport))
            return false;
        // Yes! Report now!
        return true;
    }

    private void updateEarliestNextReport() {
        Calendar cal = Calendar.getInstance();
        cal.setTime(new Date());
        cal.add(Calendar.SECOND, 15);
        earliestNextReport = cal.getTime();
    }

    public void addEvent(Beacon beacon) {
        totalEventCount.incrementAndGet();
        events.add(new Event(beacon));
        reportNow();
    }

    public void reportNow() {
        reportNow(false);
    }
    public void reportNow(boolean force) {
        // Send a report now
        if (force || shouldReportNow()) {
            // Keep a local copy of events (theoretically thread safe!)
            ArrayList<Event> eventsToSend = events;
            events = new ArrayList<Event>();

            // Send the report now in a different thread
            new EventReporter().executeOnExecutor(
                    AsyncTask.THREAD_POOL_EXECUTOR,
                    eventsToSend
            );

            // Make sure we don't send reports too often
            updateEarliestNextReport();
        }
    }

    @Override
    public String toString() {
        if (totalEventCount.get() == 0) {
            // No events yet
            return ctx.getString(
                    R.string.eventtracker__no_events
            );
        }

        // Give back event summary
        return ctx.getString(
                R.string.eventtracker__result,
                totalEventCount.get(),
                events.size(),
                preferences.getInt("report_interval", -1)
        );
    }
}
