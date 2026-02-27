import { getChatGroupId } from '../../../api';

const CATACHAT_URL = 'https://catachat.catachess.com';

export function openClassChat(classroomId: string): void {
  getChatGroupId(classroomId)
    .then(({ catchat_group_id }) => {
      if (!catchat_group_id) return;
      const token = localStorage.getItem('catachess_token') || sessionStorage.getItem('catachess_token');
      const url = `${CATACHAT_URL}/group/${catchat_group_id}${token ? `?token=${encodeURIComponent(token)}` : ''}`;
      window.open(url, '_blank', 'noopener,noreferrer');
    })
    .catch(() => {});
}
