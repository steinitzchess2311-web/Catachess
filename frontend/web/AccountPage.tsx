import React, { useEffect, useState } from 'react';
import { api } from '@ui/assets/api';

interface UserProfile {
  lichess_username: string;
  chesscom_username: string;
  fide_rating: string | number;
  cfc_rating: string | number;
  ecf_rating: string | number;
  chinese_athlete_title: string;
  fide_title: string;
  self_intro: string;
}

const AccountPage: React.FC = () => {
  const [profile, setProfile] = useState<UserProfile>({
    lichess_username: '',
    chesscom_username: '',
    fide_rating: '',
    cfc_rating: '',
    ecf_rating: '',
    chinese_athlete_title: '',
    fide_title: '',
    self_intro: '',
  });
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const data = await api.get('/user/profile');
        setProfile({
          lichess_username: data.lichess_username || '',
          chesscom_username: data.chesscom_username || '',
          fide_rating: data.fide_rating || '',
          cfc_rating: data.cfc_rating || '',
          ecf_rating: data.ecf_rating || '',
          chinese_athlete_title: data.chinese_athlete_title || '',
          fide_title: data.fide_title || '',
          self_intro: data.self_intro || '',
        });
      } catch (error) {
        console.error('Error fetching profile:', error);
      }
    };

    fetchProfile();
  }, []);

  const handleChange = (event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = event.target;
    setProfile(prevProfile => ({
      ...prevProfile,
      [name]: value,
    }));
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      // Convert rating fields to numbers before saving, if they are not empty
      const profileToSave = {
        ...profile,
        fide_rating: profile.fide_rating ? Number(profile.fide_rating) : null,
        cfc_rating: profile.cfc_rating ? Number(profile.cfc_rating) : null,
        ecf_rating: profile.ecf_rating ? Number(profile.ecf_rating) : null,
      };

      await api.put('/user/profile', profileToSave);

      // Optionally show a success notification
      console.log('Profile saved successfully!');
    } catch (error) {
      console.error('Error saving profile:', error);
      // Optionally show an error message to the user
    } finally {
      setSaving(false);
    }
  };

  return (
    <div style={{ margin: '32px auto', maxWidth: 900, padding: '0 16px' }}>
      <div
        style={{
          borderRadius: 12,
          boxShadow: '0 8px 32px 0 rgba(31, 38, 135, 0.2)',
          background: '#ffffff',
          padding: 24,
        }}
      >
        <h1 style={{ margin: '0 0 24px', fontSize: 28 }}>Edit Your Profile</h1>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
            gap: 16,
          }}
        >
          <label>
            Lichess Username
            <input
              name="lichess_username"
              value={profile.lichess_username}
              onChange={handleChange}
              style={{ width: '100%', marginTop: 6 }}
            />
          </label>
          <label>
            Chess.com Username
            <input
              name="chesscom_username"
              value={profile.chesscom_username}
              onChange={handleChange}
              style={{ width: '100%', marginTop: 6 }}
            />
          </label>
          <label>
            FIDE Rating
            <input
              name="fide_rating"
              type="number"
              value={profile.fide_rating}
              onChange={handleChange}
              style={{ width: '100%', marginTop: 6 }}
            />
          </label>
          <label>
            CFC Rating
            <input
              name="cfc_rating"
              type="number"
              value={profile.cfc_rating}
              onChange={handleChange}
              style={{ width: '100%', marginTop: 6 }}
            />
          </label>
          <label>
            ECF Rating
            <input
              name="ecf_rating"
              type="number"
              value={profile.ecf_rating}
              onChange={handleChange}
              style={{ width: '100%', marginTop: 6 }}
            />
          </label>
          <label>
            FIDE Title
            <input
              name="fide_title"
              value={profile.fide_title}
              onChange={handleChange}
              placeholder="e.g., GM, IM, FM"
              style={{ width: '100%', marginTop: 6 }}
            />
          </label>
          <label>
            Chinese Athlete Title
            <input
              name="chinese_athlete_title"
              value={profile.chinese_athlete_title}
              onChange={handleChange}
              style={{ width: '100%', marginTop: 6 }}
            />
          </label>
          <label style={{ gridColumn: '1 / -1' }}>
            Self Introduction
            <textarea
              name="self_intro"
              rows={4}
              value={profile.self_intro}
              onChange={handleChange}
              style={{ width: '100%', marginTop: 6 }}
            />
            <div style={{ fontSize: 12, color: '#666' }}>
              A brief introduction about yourself.
            </div>
          </label>
        </div>

        <div style={{ marginTop: 24, display: 'flex', justifyContent: 'flex-end' }}>
          <button
            type="button"
            onClick={handleSave}
            disabled={saving}
            style={{
              padding: '10px 18px',
              borderRadius: 8,
              border: 'none',
              background: '#2f6fed',
              color: '#fff',
              cursor: saving ? 'default' : 'pointer',
            }}
          >
            {saving ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default AccountPage;
